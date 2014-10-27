__author__ = 'mlosito'

import time
import os
from urllib2 import HTTPError
import re
import traceback

from AVCommon.logger import logging
from AVAgent.rcs_client import Rcs_client


class connection:
    host = ""
    DEFAULT = ("avmonitor", "testriteP123")
    user = "avmonitor"
    passwd = "testriteP123" # old: avmonitorp123
    operation = 'AOP_avmaster'

    rcs=[]

    def __enter__(self):
        logging.debug("DBG login %s@%s" % (self.user, self.host))
        assert connection.host
        self.conn = Rcs_client(connection.host, connection.user, connection.passwd)
        self.conn.login()
        return self.conn

    def __exit__(self, type, value, traceback):
        logging.debug("DBG logout")
        self.conn.logout()


def create_new_factory(ftype, frontend, backend, operation, target, factory, config):
    connection.host = backend
    connection.operation = operation
    with connection() as c:
        assert c
        if not c.logged_in():
            logging.warn("Not logged in")
        logging.debug(
            "DBG type: " + ftype + ", operation: " + operation + ", target: " + target + ", factory: " + factory)

        operation_id, group_id = c.operation(operation)
        if not operation_id:
            raise RuntimeError("Cannot get operations")

        # gets all the target with our name in an operation
        targets = c.targets(operation_id, target)
        logging.debug("Existing targets: %s with operation id: %s" % (targets, operation_id))
        if len(targets) > 0:
            # keep only one target

            for t in targets[1:]:
                logging.debug("Deleting target: %s" % t)
                c.target_delete(t)

            target_id = targets[0]
            logging.debug("Using target: %s" % target_id)
            agents = c.agents(target_id)

            for agent_id, ident, name in agents:
                logging.debug("DBG   %s %s %s" % (agent_id, ident, name))
                if name.startswith(factory):
                    logging.debug("- Delete instance: %s %s" % (ident, name))
                    c.instance_delete(agent_id)
        else:
            logging.debug("- Create target: %s" % target)
            target_id = c.target_create(
                operation_id, target, 'made by vmavtest at %s' % time.ctime())

        factory_id, ident = c.factory_create(
            operation_id, target_id, ftype, factory,
            'made by vmavtestat at %s' % time.ctime()
        )

        with open(config) as f:
            conf = f.read()

        conf = re.sub(
            r'"host": ".*"', r'"host": "%s"' % frontend, conf)

        #logging.debug("conf: %s" % conf)
        c.factory_add_config(factory_id, conf)
        if not os.path.exists('build'):
            os.mkdir('build')
        with open('build/config.actual.json', 'wb') as f:
            f.write(conf)

        return (target_id, factory_id, ident)


def get_factory(factory_id, backend, operation):
    connection.host = backend
    connection.operation = operation
    with connection() as c:
        factories = c.search_factories_by_name(factory_id)
        logging.debug("- factories: %s" % factories)
        #I also assume there is only a single factory with that name
        #this is partially guaranteed because the factory contains the useful part of the operation name
        if len(factories) == 0:
            return None
        else:
            return factories[0]


def build_agent(factory, hostname, param, result_adder_function, zipfilename, melt=None, kind="silent", tries=0, use_cache=False, appname = None):
    with connection() as c:

        try:
            #nel caso di una build server, voglio usare un caching, quindi controllo se c'e' gia' un build pronto
            if use_cache:
                if os.path.exists(zipfilename):
                    logging.debug("- Using file '%s' from cache" % zipfilename)
                    return zipfilename
                else:
                    logging.debug("- Creating new file '%s' and storing to cache" % zipfilename)
            else:
                logging.debug("- Creating new file '%s' (no cache)" % zipfilename)
            if os.path.exists(zipfilename):
                os.remove(zipfilename)
            if not os.path.exists(os.path.dirname(zipfilename)):
                os.mkdir(os.path.dirname(zipfilename))
            if kind=="melt" and melt:
                logging.debug("- Melt build with: %s" % melt)
                if not appname:
                    appname = "exp_%s" % hostname
                param['melt']['appname'] = appname
                param['melt']['url'] = "http://%s/%s/" % (c.host, appname)
                if 'deliver' in param:
                    param['deliver']['user'] = c.myid
                r = c.build_melt(factory, param, melt, zipfilename)
            else:
                logging.debug("- Silent build for factory: %s", factory)
                r = c.build(factory, param, zipfilename)

        #here ML removed lines to statiacally check extraction

        except HTTPError as err:
            logging.debug("DBG trace %s" % traceback.format_exc())
            if tries <= 3:
                tries += 1
                logging.debug("DBG problem building scout. tries number %s" % tries)
                build_agent(factory, result_adder_function, zipfilename, melt, kind, tries)
            else:
                if result_adder_function:
                    result_adder_function("+ ERROR SCOUT BUILD AFTER %s BUILDS" % tries)
                else:
                    logging.debug("+ ERROR SCOUT BUILD AFTER %s BUILDS" % tries)
                raise err
        except Exception, e:
            logging.debug("DBG trace %s" % traceback.format_exc())
            if result_adder_function:
                result_adder_function("+ ERROR SCOUT BUILD EXCEPTION RETRIEVED")
            else:
                logging.debug("+ ERROR SCOUT BUILD EXCEPTION RETRIEVED")
            raise e
        return zipfilename

def create_user(user_name, passwd = connection.passwd, operation = connection.operation):
    logging.debug("create_user_machine")

    privs = [
        'ADMIN', 'ADMIN_USERS', 'ADMIN_OPERATIONS', 'ADMIN_TARGETS', 'ADMIN_AUDIT',
        'ADMIN_LICENSE', 'SYS', 'SYS_FRONTEND', 'SYS_BACKEND', 'SYS_BACKUP',
        'SYS_INJECTORS', 'SYS_CONNECTORS', 'TECH',
        'TECH_FACTORIES', 'TECH_BUILD', 'TECH_CONFIG', 'TECH_EXEC', 'TECH_UPLOAD',
        'TECH_IMPORT', 'TECH_NI_RULES', 'VIEW', 'VIEW_ALERTS', 'VIEW_FILESYSTEM',
        'VIEW_EDIT', 'VIEW_DELETE', 'VIEW_EXPORT', 'VIEW_PROFILES']

    assert user_name
    assert passwd

    connection.user = user_name
    connection.passwd = passwd

    user_exists = False
    try:
        with connection() as c:
            logging.debug("LOGIN SUCCESS")
            user_exists = True
    except:
        pass

    if not user_exists:
        logging.debug("creating user")
        connection.user, connection.passwd = connection.DEFAULT
        with connection() as c:
            ret = c.operation(operation)
            op_id, group_id = ret
            assert op_id and group_id

            c.user_create(user_name, passwd, privs, group_id)

    connection.user = user_name
    connection.passwd = passwd
    return True
