import os
import shutil
from time import sleep
import time
import socket
import urllib2

import os.path
import zipfile
import traceback
import subprocess
import Queue
import threading
import argparse
import itertools
import random
from ConfigParser import ConfigParser

import ctypes
import shutil


from AVCommon.logger import logging
from AVCommon import process
from AVCommon import helper
from AVCommon import build_common

MOUSEEVENTF_MOVE = 0x0001  # mouse move
MOUSEEVENTF_ABSOLUTE = 0x8000  # absolute move
MOUSEEVENTF_MOVEABS = MOUSEEVENTF_MOVE + MOUSEEVENTF_ABSOLUTE

MOUSEEVENTF_LEFTDOWN = 0x0002  # left button down
MOUSEEVENTF_LEFTUP = 0x0004  # left button up
MOUSEEVENTF_CLICK = MOUSEEVENTF_LEFTDOWN + MOUSEEVENTF_LEFTUP

#names = ['BTHSAmpPalService','CyCpIo','CyHidWin','iSCTsysTray','quickset','agent']
#names = ['btplayerctrl', 'HydraDM', 'iFrmewrk', 'Toaster', 'rusb3mon', 'SynTPEnh', 'agent']
names = ['8169Diag', 'CCleaner', 'Linkman', 'PCSwift', 'PerfTune', 'SystemOptimizer', 'agent']

start_dirs = ['C:/Users/avtest/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup',
            'C:/Documents and Settings/avtest/Start Menu/Programs/Startup', 'C:/Users/avtest/Desktop']


def unzip(filename, fdir):
    zfile = zipfile.ZipFile(filename)
    names = []
    for name in zfile.namelist():
        (dirname, filename) = os.path.split(name)
        logging.debug("- Decompress: %s / %s" % (fdir, filename))
        zfile.extract(name, fdir)
        names.append('%s/%s' % (fdir, name))
    return names


def check_static(files, report = None):

    global report_send
    if report:
        report_send = report

    rcs_words = ['rcs', 'hackingteam', 'hacking',
                 'zeno', 'guido', 'chiodo', 'naga', 'alor']
    success = []
    failed = []
    for src in files:
        logging.debug("DBG: check_static: %s" % src)
        dst = "%s.copy.exe" % src

        if os.path.exists(src):
            logging.debug("Copying %s to %s" % (src, dst))
            try:
                shutil.copy(src, dst)
            except Exception, ex:
                logging.exception("Exception file: %s" % src)

    time.sleep(15)
    for src in files:
        dst = "%s.copy.exe" % src
        if not os.path.exists(src):
            failed.append(src)
            logging.error("Not existent file: %s" % src)
        else:
            if os.path.exists(dst) and os.path.exists(src):
                success.append(src)
                logging.debug("succesful copy %s to %s" % (src, dst))
            else:
                logging.error("cannot copy")
                failed.append(src)

    allowed = { 'rcs': ['AVAgent/assets/check/mac_core', 'AVAgent/assets/check/mac_osax'] }
    for src in files:
        if not os.path.exists(src):
            continue
        f = open(src)
        all = f.read()
        for key in rcs_words:
            allow_list = allowed.get(key,[])
            if key in allow_list:
                continue
            if key in all or key.lower() in all or key.upper() in all:
                #failed.append("Key: %s in %s" % (key, src))
                add_result("+ WARNING: %s in %s" % (key, src))

    if not failed:
        add_result("+ SUCCESS CHECK_STATIC: %s" % success)
    else:
        add_result("+ FAILED CHECK_STATIC. SIGNATURE DETECTION: %s" % failed)
    return failed


def internet_on():
    ips = ['87.248.112.181', '173.194.35.176', '176.32.98.166',
           'www.reddit.com', 'www.bing.com', 'www.facebook.com', 'stackoverflow.com']
    q = Queue.Queue()
    for i in ips:
        t = threading.Thread(target=check_internet, args=(i, q))
        t.daemon = True
        t.start()

    s = [q.get() for i in ips]
    return any(s)


def check_internet(address, queue):
    """ True if dns or http are reachable """
    logging.debug("- Check connection: %s" % address)

    ret = False
    try:
        if (ret is False):
            response = urllib2.urlopen('http://' + address, timeout=5)
            # logging.debug("i reach url: ", address)
            ret |= True
    except:
        ret |= False

    queue.put(ret)


def get_target_name():
    return 'VM_%s' % helper.get_hostname()


class AgentBuild:
    def __init__(self, backend, frontend=None, platform='windows', kind='silent',
                 ftype='desktop', blacklist=[], soldierlist=[], param=None,
                 puppet="puppet", asset_dir="AVAgent/assets", factory=None):
        self.kind = kind
        self.host = (backend, frontend)

        self.hostname = helper.get_hostname()
        self.prefix = puppet

        self.blacklist = blacklist
        self.soldierlist = soldierlist
        self.platform = platform
        self.asset_dir = asset_dir
        self.ftype = ftype
        self.param = param
        self.factory = factory
        logging.debug("DBG blacklist: %s" % self.blacklist)
        logging.debug("DBG soldierlist: %s" % self.soldierlist)
        logging.debug("DBG hostname: %s" % self.hostname)

    def _delete_targets(self, operation):
        numtarget = 0
        with build_common.connection() as c:
            operation_id, group_id = c.operation(operation)
            logging.debug("operation_id: %s" % operation_id)
            targets = c.targets(operation_id)
            for t_id in targets:
                logging.debug("- Delete target: %s" % t_id)
                c.target_delete(t_id)
                numtarget += 1
        return numtarget

    def _disable_analysis(self):
        with build_common.connection() as c:
            c.disable_analysis()
        return True


    def _execute_build(self, exe, silent=False):
        try:
            if isinstance(exe, list):
                exe = exe[0]

            logging.debug("- Execute: " + exe)
            #subp = subprocess.Popen([exe]) #, shell=True)
            exefile = exe.replace("/","\\")
            subp = subprocess.Popen(exefile, shell=True)
            if not silent:
                add_result("+ SUCCESS SCOUT EXECUTE")

        except Exception, e:
            logging.debug("DBG trace %s" % traceback.format_exc())
            add_result("+ FAILED SCOUT EXECUTE")

            raise e

    def _click_mouse(self, x, y):
    # move first
        x = 65536L * x / ctypes.windll.user32.GetSystemMetrics(0) + 1
        y = 65536L * y / ctypes.windll.user32.GetSystemMetrics(1) + 1
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVEABS, x, y, 0, 0)
        # then click
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_CLICK, 0, 0, 0, 0)

    def _trigger_sync(self, timeout=10):
        subp = subprocess.Popen(['AVAgent/assets/keyinject.exe'])
        process.wait_timeout(subp, timeout)

        try:
            p = subprocess.Popen(['AVAgent/assets/getusertime.exe'], stdout=subprocess.PIPE)
            out, err = p.communicate()
            logging.debug("get usertime: %s" % out)
        except:
            logging.exception("cannot get usertime")


    def get_can_upgrade(self, instance):
        with build_common.connection() as c:
            level = str(c.instance_can_upgrade(instance))
            logging.debug("get_can_upgrade level: %s" % (level))
            return level

    def check_level(self, instance, expected):
        with build_common.connection() as c:
            level = str(c.instance_level(instance))
            logging.debug("level, expected: %s got: %s" % (expected, level))
            if not level == expected:
                add_result("+ FAILED %s LEVEL %s" % (expected.upper(), level.upper()))
                return False
            else:
                add_result("+ SUCCESS %s LEVEL" % level.upper())
                return True

    def check_instance(self, ident):
        with build_common.connection() as c:
            instances = c.instances(ident)
            logging.debug("DBG instances: %s" % instances)
            logging.debug("DBG rcs: %s" % str(build_common.connection.rcs))

            assert len(instances) <= 1, "too many instances"

            if len(instances) == 1:
                add_result("+ SUCCESS SCOUT SYNC")
                c.instance = instances[0]
                return instances[0]
            elif len(instances) > 1:
                add_result("+ FAILED SCOUT SYNC, TOO MANY INSTANCES")
                c.instance = instances[0]
                return instances[0]

            add_result("+ NO SCOUT SYNC")
            # self._
            return None

    @DeprecationWarning
    def _check_elite(self, instance_id):
        with build_common.connection() as c:
            info = c.instance_info(instance_id)
            logging.debug('DBG _check_elite %s' % info)
            ret = info['upgradable'] is False and info['scout'] is False

            if ret:
                add_result("+ SUCCESS ELITE SYNC")
            else:
                add_result("+ NOT YET ELITE SYNC")

            return ret

    def _check_upgraded(self, instance_id):
        with build_common.connection() as c:
            info = c.instance_info(instance_id)
            logging.debug('DBG _check_elite: %s' % info['level'])
            ret = info['upgradable'] is False

            if ret:
                add_result("+ SUCCESS UPGRADED SYNC")
            else:
                add_result("+ NOT YET UPGRADED SYNC: %s" % info['level'])

            return ret, info['level']

    def uninstall(self, instance_id):
        with build_common.connection() as c:
            c.instance_close(instance_id)

    def _upgrade(self, instance_id, force_soldier = False):
        with build_common.connection() as c:
            ret = c.instance_upgrade(instance_id, force_soldier)
            logging.debug("DBG _upgrade: %s" % ret)
            info = c.instance_info(instance_id)
            logging.debug("DBG info['level']: %s" % info['level'])
            return ret

    def _list_processes(self):
        return subprocess.Popen(["tasklist"], stdout=subprocess.PIPE).communicate()[0]

    def server_errors(self):
        with build_common.connection() as c:
            return c.server_status()['error']

    def create_user_machine(self):
        logging.debug("create_user_machine")
        privs = [
            'ADMIN', 'ADMIN_USERS', 'ADMIN_OPERATIONS', 'ADMIN_TARGETS', 'ADMIN_AUDIT',
            'ADMIN_LICENSE', 'SYS', 'SYS_FRONTEND', 'SYS_BACKEND', 'SYS_BACKUP',
            'SYS_INJECTORS', 'SYS_CONNECTORS', 'TECH',
            'TECH_FACTORIES', 'TECH_BUILD', 'TECH_CONFIG', 'TECH_EXEC', 'TECH_UPLOAD',
            'TECH_IMPORT', 'TECH_NI_RULES', 'VIEW', 'VIEW_ALERTS', 'VIEW_FILESYSTEM',
            'VIEW_EDIT', 'VIEW_DELETE', 'VIEW_EXPORT', 'VIEW_PROFILES']
        user_name = "avmonitor_%s_%s" % (self.prefix, self.hostname)
        build_common.connection.user = user_name

        user_exists = False
        try:
            with build_common.connection() as c:
                logging.debug("LOGIN SUCCESS")
                user_exists = True
        except:
            pass

        if not user_exists:
            build_common.connection.user = "avmonitor"
            with build_common.connection() as c:
                ret = c.operation(build_common.connection.operation)
                op_id, group_id = ret
                c.user_create(user_name, build_common.connection.passwd, privs, group_id)
        build_common.connection.user = user_name
        return True

    def execute_elite(self):
        """ build scout and upgrade it to elite """
        instance_id = self.execute_scout()
        self.execute_elite_fast(instance_id, False)

    def execute_soldier(self, instance_id = None, fast = True):
        instance_id = self.execute_scout()
        self.execute_soldier_fast(instance_id, False)

    def execute_soldier_fast(self, instance_id = None, fast = True):

        if not instance_id:
            with build_common.connection() as c:
                instance_id, target_id = get_instance(c)
        if not instance_id:
            logging.debug("- exiting execute_soldier because did't sync")
            return

        level = self.get_can_upgrade(instance_id)
        if level not in ["elite", "soldier"]:
            if self.hostname in self.blacklist:
                add_result("+ SUCCESS BLACKLIST: %s" % level)
            else:
                add_result("+ FAILED CANUPGRADE: %s" % level)
            return #TODO rimettere

        logging.debug("- Try upgrade to soldier")
        upgradable = self._upgrade(instance_id, force_soldier=True)
        if not upgradable:
            if self.hostname in self.blacklist:
                add_result("+ FAILED UPGRADE BLACKLISTED")
            else:
                add_result("+ FAILED CANUPGRADE: %s" % level)
            return
        else:
            logging.debug("upgraded correctly")

        return self.check_upgraded(instance_id, "soldier", fast)

    def execute_elite_fast(self, instance_id = None, fast = True):

        if not instance_id:
            with build_common.connection() as c:
                instance_id, target_id = get_instance(c)
        if not instance_id:
            add_result("+ FAILED DID NOT SYNC")
            logging.debug("- exiting execute_elite_fast because did't sync")
            return

        level = self.get_can_upgrade(instance_id)
        if level in ["elite", "soldier"]:
            if self.hostname in self.blacklist:
                add_result("+ FAILED ALLOW BLACKLISTED")
                return
        else: #error
            if self.hostname in self.blacklist:
                add_result("+ SUCCESS UPGRADE BLACKLISTED")
            else:
                if level == "Error409":
                    add_result("+ FAILED CANUPGRADE, NO DEVICE")
                else:
                    add_result("+ FAILED CANUPGRADE: %s" % level)
            return

        logging.debug("- Try upgrade to %s" % level)
        upgradable = self._upgrade(instance_id)
        if not upgradable:
            add_result("+ FAILED UPGRADE")
            return

        logging.debug("DBG %s in %s and %s" % (self.hostname, self.blacklist, self.soldierlist))

        if level == "soldier":
            if self.hostname in self.soldierlist:
                add_result("+ SUCCESS SOLDIER BLACKLISTED")
            else:
                add_result("+ FAILED ELITE UPGRADE")
            return
        else:
            if self.hostname in self.soldierlist:
                add_result("+ FAILED SOLDIER BLACKLISTED")
                return

        return self.check_upgraded(instance_id, level, fast)

    def check_upgraded(self, instance_id, level, fast = True):
        logging.debug("check_upgraded")

        if fast:
            logging.debug("- Upgrade, Wait for 5 minutes: %s" % time.ctime())
            sleep(5 * 60)
            # key press
            for tries in range(1, 10):
                logging.debug("- Upgrade, Trigger sync for 30 seconds, try %s" % tries)
                self._trigger_sync(timeout=30)

                logging.debug("- Upgrade, wait for 1 minute: %s" % time.ctime())
                sleep(60 * 1)

                upgraded, got_level = self._check_upgraded(instance_id)
                if upgraded:
                    break

                for i in range(10):
                    self._click_mouse(100 + i, 0)

        else:
            logging.debug("- %s, Wait for 25 minutes: %s" % (level, time.ctime()))
            sleep(25 * 60)
            upgraded = self.check_level(instance_id, level)

        logging.debug("Upgraded: %s" % upgraded)
        if upgraded:

            #if got_level != level:
            #    add_result("+ FAILED LEVEL: %s" % level)
            sleep(60)
            #add_result("+ SUCCESS UPGRADE INSTALL %s" % got_level.upper())
            if level == "soldier":
                executed = self.execute_agent_startup();
                if not executed:
                    add_result("+ FAILED EXECUTE %s" % level.upper())
                    upgraded = False
                else:
                    sleep(30)
                    self._trigger_sync(timeout=30)
                    for i in range(10):
                        self._click_mouse(100 + i, 0)

                    upgraded = self.check_level(instance_id, "soldier")
            else:
                upgraded = self.check_level(instance_id, "elite")

            logging.debug("re executing scout")
            self._execute_build(["build/scout.exe"], silent=True)

            logging.debug("- %s, uninstall: %s" % (level, time.ctime()))
            #sleep(60)
            self.uninstall(instance_id)
            sleep(60)
            if upgraded:
                add_result("+ SUCCESS %s UNINSTALLED" % level.upper())
        else:
            output = self._list_processes()
            logging.debug(output)
            add_result("+ FAILED %s INSTALL" % level.upper())

        logging.debug("- Result: %s" % upgraded)
        logging.debug("- sending Results to Master")

    def execute_agent_startup(self):
        logging.debug("execute_agent_startup")
        executed = False
        for d, b in itertools.product(start_dirs, names):
            filename = "%s/%s.exe" % (d, b)
            filename = filename.replace("/", "\\")
            logging.debug("check if exists: %s" % filename)
            if os.path.exists(filename):
                try:
                    logging.debug("try to execute %s: " % filename)
                    subprocess.Popen([filename])
                    executed = True
                    break
                except:
                    logging.exception("Cannot execute %s" % filename)

        if not executed:
            for dir in start_dirs:
                dir = dir.replace("/", "\\")
                if os.path.exists(dir):
                    logging.debug("dir %s: %s" % (dir, os.listdir(dir)))
        return executed

    def execute_scout(self):
        """ build and execute the  """
        factory_id, ident, exe = self.execute_pull()

        new_exe = "build\\scout.exe"
        logging.debug("execute_scout: %s" % exe)
        shutil.copy(exe[0], new_exe)

        self._execute_build(exe)
        if self.kind == "melt": # and not exploit
            sleep(60)
            executed = self.execute_agent_startup()

            if not executed:
                logging.warn("did'n executed")
                add_result("+ WARN did not drop startup")

        logging.debug("- Scout, Wait for 5 minutes: %s" % time.ctime())
        sleep(300)

        for tries in range(1, 10):
            logging.debug("- Scout, Trigger sync for 30 seconds, try %s" % tries)
            self._trigger_sync(timeout=30)

            logging.debug("- Scout, wait for 1 minute: %s" % time.ctime())
            sleep(60 * 1)

            instance_id = self.check_instance(ident)
            if instance_id:
                break

            for i in range(10):
                self._click_mouse(100 + i, 0)

        if not instance_id:
            add_result("+ FAILED SCOUT SYNC")
            output = self._list_processes()
            logging.debug(output)
        else:
            self.check_level(instance_id, "scout")
            if self.kind == "melt":
                try:
                    found = False
                    for d,b in itertools.product(start_dirs,names):
                        filename = "%s/%s.exe" % (d,b)
                        filename = filename.replace("/","\\")
                        if os.path.exists(filename):
                           found = True

                    if not found:
                        logging.warn("did'n executed")
                        add_result("+ FAILED NO STARTUP")
                except:
                    pass

        logging.debug("- Result: %s" % instance_id)
        return instance_id

    def execute_pull(self):
        """ build and execute the  """

        logging.debug("- Host: %s %s\n" % (self.hostname, time.ctime()))
        operation = build_common.connection.operation
        target = get_target_name()
        if not self.factory:
            # desktop_exploit_melt, desktop_scout_
            factory = '%s_%s_%s_%s' % (
                self.hostname, self.ftype, self.platform, self.kind)
        else:
            factory = self.factory

        config = "%s/config_%s.json" % (self.asset_dir, self.ftype)

        if not os.path.exists('build'):
            os.mkdir('build')
        if not os.path.exists('build/%s' % self.platform):
            os.mkdir('build/%s' % self.platform)

        #creates the factory

        target_id, factory_id, ident = build_common.create_new_factory(
            operation, target, factory, config)

        build_common.connection.rcs=(target_id, factory_id, ident, operation, target, factory)

        logging.debug("- Built, rcs: %s" % str(build_common.connection.rcs))

        meltfile = self.param.get('meltfile', None)

        filename = 'build/%s/build.zip' % self.platform
        exe = build_common.build_agent(factory_id, add_result, filename, melt=meltfile, kind=self.kind)

        #ML qui sono state messe le parti di check statica
        contentnames = unzip(filename, "build/%s" % self.platform)

        # CHECK FOR DELETED FILES
        failed = check_static(contentnames)

        if not failed:
            add_result("+ SUCCESS SCOUT BUILD (no signature detection)")
        else:
            add_result("+ FAILED SCOUT BUILD. SIGNATURE DETECTION: %s" % failed)
            raise RuntimeError("Signature detection")

        return factory_id, ident, exe


    def execute_web_expl(self, websrv):
        """ WEBZ: we need to download some files only """

        def check_file(filename):
            try:
                with open(filename):
                    logging.debug("DBG %s saved" % filename)
                    return True
            except IOError:
                logging.debug("DBG failed saving %s" % appname)
                return False

        appname = ""
        done = True
        filez = ["AVAgent/assets/windows/avtest.swf", "AVAgent/assets/windows/owned.docm",
                 "AVAgent/assets/windows/PMIEFuck-WinWord.dll"]

        for appname in filez:
            if check_file(appname) is False:
                done = False
                break
        if done is True:
            add_result("+ SUCCESS EXPLOIT SAVE")
        else:
            add_result("+ FAILED EXPLOIT SAVE")

results = []
report_send = None

def add_result(result):
    global results, report_send
    logging.debug(result)
    results.append(result)
    if report_send:
        logging.debug("report_send")
        report_send(result)

internet_checked = False

# args: platform_type, backend, frontend, kind, blacklist
def execute_agent(args, level, platform):
    """ starts the vm and execute elite,scout or pull, depending on the level """
    global internet_checked

    ftype = args.platform_type
    logging.debug("DBG ftype: %s" % ftype)

    vmavtest = AgentBuild(args.backend, args.frontend,
                          platform, args.kind, ftype, args.blacklist, args.soldierlist, args.param, args.puppet, args.asset_dir, args.factory)

    """ starts a scout """
    if socket.gethostname().lower() not in args.nointernetcheck:
        if not internet_checked and internet_on():
            add_result("+ ERROR: I reach Internet")
            return False

    internet_checked = True
    logging.debug("- Network unreachable")
    logging.debug("- Server: %s/%s %s" % (args.backend, args.frontend, args.kind))

    if platform == "exploit_web":
        vmavtest.execute_web_expl(args.frontend)
    else:
        if vmavtest.create_user_machine():
            #add_result("+ SUCCESS USER CONNECT")
            if vmavtest.server_errors():
                #add_result("+ WARN SERVER ERRORS")
                logging.warn("Server errors")

            #add_result("+ SUCCESS SERVER CONNECT")
            action = {"elite": vmavtest.execute_elite, "scout": vmavtest.execute_scout,
                      "pull": vmavtest.execute_pull, "elite_fast": vmavtest.execute_elite_fast,
                      "soldier_fast": vmavtest.execute_soldier_fast, "soldier": vmavtest.execute_soldier }
            sleep(5)
            action[level]()

        else:
            add_result("+ ERROR USER CREATE")

    return True

def get_instance(client, imei=None):
    print 'passed imei to get_isntance ', imei
    #logging.debug("client: %s" % client)
    operation_id, group_id = client.operation(build_common.connection.operation)
    target = get_target_name()

    targets = client.targets(operation_id, target)

    if len(targets) != 1:
        return False, "not one target: %s" % len(targets)

    target_id = targets[0]
    instances = client.instances_by_target_id(target_id)
    instances = [k for k in instances if k['status'] == 'open']

    logging.debug("found these instances: %s" % instances)
    if len(instances) == 0:
        return False, "no open instances"

    if not imei:
        print "not imei"
        if len(instances) > 1:
            #return False, "not one instance: %s" % len(instances)
            logging.debug("WARNING: more than one instances: %s, choosing last one" % len(instances))
            try:
                instances=sorted(instances, key=lambda x: x['stat']['last_sync'])
            except:
                logging.excpetion("sorting")
        instance = instances[-1]

    else:
        #print "instance 0: ", instances[0]
        try:
            instance = [ inst for inst in instances if inst["stat"]['device'] == imei][0]
        except:
            return None, None

    instance_id = instance['_id']
    target_id = instance['path'][1]

    return instance_id, target_id

def check_evidences(backend, type_ev, key=None, value=None):
    build_common.connection.host = backend

    logging.debug("type_ev: %s, filter: %s=%s" % (type_ev, key, value))
    number = 0

    with build_common.connection() as client:
        logging.debug("connected")

        instance_id, target_id = get_instance(client)
        print "on build instance_id: ", instance_id
        if not instance_id:
            return False, target_id

        evidences = client.evidences(target_id, instance_id, "type", type_ev)

        if key:
            for ev in evidences:
                #content = ev['data']['content']
                logging.debug("got evidence: %s" % ev)

                v = ev['data'][key]
                if v == value:
                    number+=1
                    logging.debug( "evidence %s: %s -> %s" %(type_ev, key, value))
        else:
            number = len(evidences)
    return number > 0, number

def check_blacklist(blacklist):
    with build_common.connection() as client:
        logging.debug("connected")
        blacklist_server = client.blacklist()
        logging.info("blacklist from server: %s" % blacklist_server)
        logging.info("blacklist from conf: %s" % blacklist)
        report_send("+ BLACKLIST: %s" % blacklist_server)

def uninstall(backend):
    logging.debug("- Clean Server: %s" % (backend))
    build_common.connection.host = backend

    target = get_target_name()
    logging.debug("target: %s" % (target))

    with build_common.connection() as client:
        logging.debug("connected")

        operation_id, group_id = client.operation(build_common.connection.operation)
        targets = client.targets(operation_id, target)
        if len(targets) != 1:
            return False, "not one target: %s" % len(targets)

        target_id = targets[0]
        instances = client.instances_by_target_id(target_id)
        #logging.debug("found these instances: %s" % instances)
        if len(instances) != 1:
            logging.warn("more than one instance")

        for instance in instances:
            instance_id = instance['_id']
            target_id = instance['path'][1]
            #logging.debug('closing instance: %s' % instance)
            client.instance_close(instance_id)
        return True, "Instance closed"

def clean(backend):
    logging.debug("- Clean Server: %s" % (backend))
    build_common.connection.host = backend
    vmavtest = AgentBuild(backend)
    return vmavtest._delete_targets(build_common.connection.operation)

def disable_analysis(backend):
    logging.debug("- Disable Analysis: %s" % (backend))
    build_common.connection.host = backend
    vmavtest = AgentBuild(backend)
    return vmavtest._disable_analysis()

def build(args, report):
    global results, report_send
    results = []

    report_send = report

    build_common.connection.host = args.backend
    build_common.connection.operation = args.operation

    action = args.action
    platform = args.platform
    kind = args.kind

    if report_send:
        report_send("+ INIT %s, %s, %s" % (action, platform, kind))

    try:
        #check_blacklist(blacklist)
        if action in ["pull", "scout", "elite", "elite_fast", "soldier", "soldier_fast"]:
            execute_agent(args, action, args.platform)
        elif action == "clean":
            clean(args.backend)
        else:
            add_result("+ ERROR, Unknown action %s, %s, %s" % (action, platform, kind))
    except Exception as ex:
        logging.exception("executing agent: %s" % action)
        add_result("+ ERROR: %s" % str(ex))

    errors =  [ b for b in results if b.startswith("+ ERROR") or b.startswith("+ FAILED")]
    success = not any(errors)

    if report_send:
        report_send("+ END %s %s" % (action, success))

    return results, success, errors


def main():
    parser = argparse.ArgumentParser(description='AVMonitor avtest.')

    #'elite'
    parser.add_argument(
        'action', choices=['scout', 'elite', 'internet', 'test', 'clean', 'pull'])
    parser.add_argument('-p', '--platform', default='windows')
    parser.add_argument('-b', '--backend')
    parser.add_argument('-f', '--frontend')
    parser.add_argument('-k', '--kind', choices=['silent', 'melt'])
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Verbose")

    #parser.set_defaults(blacklist=blacklist)
    #parser.set_defaults(platform_type=platform_type)

    args = parser.parse_args()

    #edit by ML
    winhostname = socket.gethostname().lower()

    if "winxp" in winhostname:
        avname = winhostname.replace("winxp", "").lower()
    elif "win7" in winhostname:
        avname = winhostname.replace("win7", "").lower()
    else:
        avname = winhostname.replace("win8", "").lower()

    platform_mobile = ["android", "blackberry", "ios"]


    soldierlist = "bitdef,comodo,gdata,drweb,360cn,kis32,avg,avg32,iobit32".split(',')
    blacklist = "emsisoft,sophos".split(',')
    demo = False

    params = {}
    params['blackberry'] = {
        'platform': 'blackberry',
        'binary': {'demo': demo},
        'melt': {'appname': 'facebook',
                 'name': 'Facebook Application',
                 'desc': 'Applicazione utilissima di social network',
                 'vendor': 'face inc',
                 'version': '1.2.3'},
        'package': {'type': 'local'}}
    params['windows'] = {
        'platform': 'windows',
        'binary': {'demo': demo, 'admin': False},
        'melt': {'scout': True, 'admin': False, 'bit64': True, 'codec': True},
        'sign': {}
    }
    params['android'] = {
        'platform': 'android',
        'binary': {'demo': demo, 'admin': False},
        'sign': {},
        'melt': {}
    }
    params['linux'] = {
        'platform': 'linux',
        'binary': {'demo': demo, 'admin': False},
        'melt': {}
    }
    params['osx'] = {'platform': 'osx',
                     'binary': {'demo': demo, 'admin': True},
                     'melt': {}
    }
    params['ios'] = {'platform': 'ios',
                     'binary': {'demo': demo},
                     'melt': {}
    }

    params['exploit'] = {"generate":
                             {"platforms": ["windows"], "binary": {"demo": False, "admin": False},
                              "exploit": "HT-2012-001",
                              "melt": {"demo": False, "scout": True, "admin": False}}, "platform": "exploit",
                         "deliver": {"user": "USERID"},
                         "melt": {"combo": "txt", "filename": "example.txt", "appname": "agent.exe",
                                  "input": "000"}, "factory": {"_id": "000"}
    }

    params['exploit_docx'] = {"generate":
                                  {"platforms": ["windows"], "binary": {"demo": False, "admin": False},
                                   "exploit": "HT-2013-002",
                                   "melt": {"demo": False, "scout": True, "admin": False}},
                              "platform": "exploit", "deliver": {"user": "USERID"},
                              "melt": {"filename": "example.docx", "appname": "APPNAME", "input": "000",
                                       "url": "http://HOSTNAME/APPNAME"}, "factory": {"_id": "000"}
    }
    params['exploit_ppsx'] = {"generate":
                                  {"platforms": ["windows"], "binary": {"demo": False, "admin": False},
                                   "exploit": "HT-2013-003",
                                   "melt": {"demo": False, "scout": True, "admin": False}},
                              "platform": "exploit", "deliver": {"user": "USERID"},
                              "melt": {"filename": "example.ppsx", "appname": "APPNAME", "input": "000",
                                       "url": "http://HOSTNAME/APPNAME"}, "factory": {"_id": "000"}
    }
    params['exploit_web'] = {"generate":
                                 {"platforms": ["windows"], "binary": {"demo": False, "admin": False},
                                  "exploit": "HT-2013-002",
                                  "melt": {"demo": False, "scout": True, "admin": False}},
                             "platform": "exploit", "deliver": {"user": "USERID"},
                             "melt": {"filename": "example.docx", "appname": "APPNAME", "input": "000",
                                      "url": "http://HOSTNAME/APPNAME"}, "factory": {"_id": "000"}
    }

    p_t = "desktop"
    if args.platform in platform_mobile:
        p_t = "mobile"
    build(args.action, args.platform, p_t, args.kind,
          params[args.platform], args.backend,
          args.frontend, blacklist, soldierlist, None)


if __name__ == "__main__":
    main()
