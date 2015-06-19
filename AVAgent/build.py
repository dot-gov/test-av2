import os
from time import sleep
import time
import socket
import urllib2

import os.path
import traceback
import subprocess
import Queue
import threading
import itertools

import ctypes
import shutil
import glob
from AVAgent import util_agent
from AVCommon.av import AV, UndefinedAV

from AVCommon.logger import logging
from AVCommon import process
from AVCommon import helper
from AVCommon import build_common
from AVCommon import utils
from AVCommon import config

MOUSEEVENTF_MOVE = 0x0001  # mouse move
MOUSEEVENTF_ABSOLUTE = 0x8000  # absolute move
MOUSEEVENTF_MOVEABS = MOUSEEVENTF_MOVE + MOUSEEVENTF_ABSOLUTE

MOUSEEVENTF_LEFTDOWN = 0x0002  # left button down
MOUSEEVENTF_LEFTUP = 0x0004  # left button up
MOUSEEVENTF_CLICK = MOUSEEVENTF_LEFTDOWN + MOUSEEVENTF_LEFTUP

#names = ['BTHSAmpPalService','CyCpIo','CyHidWin','iSCTsysTray','quickset','agent']
#names = ['btplayerctrl', 'HydraDM', 'iFrmewrk', 'Toaster', 'rusb3mon', 'SynTPEnh', 'agent']
#names = ['8169Diag', 'CCleaner', 'Linkman', 'PCSwift', 'PerfTune', 'SystemOptimizer', 'agent']
#names = ['ChipUtil', 'SmartDefrag', 'DiskInfo', 'EditPad', 'TreeSizeFree', 'bkmaker', 'agent']
#9_6 beta
#names = ['bleachbit', 'BluetoothView', 'CPUStabTest', 'MzRAMBooster', 'RealTemp', 'ultradefrag', 'agent']
#9_6
names = ['bleachbit', 'BluetoothView', 'dotNETInspector', 'MzRAMBooster', 'RealTemp', 'ultradefrag', 'agent']

start_dirs = ['C:/Users/avtest/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup',
            'C:/Documents and Settings/avtest/Start Menu/Programs/Startup' ] #, 'C:/Users/avtest/Desktop']


def unzip(filename, fdir):
    return utils.unzip(filename, fdir, logging.debug)


def add_agent_exe(files, files_to_check):
    # for retrocompatibility, we add an agent.exe if it is not present. This is not added to the current list of files
    agent_exe_found = False
    for src in files:
        if src.endswith("\\agent.exe"):
            agent_exe_found = True
    if not agent_exe_found:
        for src in files:
            if os.path.exists(src) and str(src).endswith(".exe"):
                dst = os.path.join(os.path.dirname(src), "agent.exe")
                files_to_check.add(dst)
                logging.debug("Creating one agent.exe - Copying %s to %s" % (src, dst))
                try:
                    shutil.copy(src, dst)
                    break
                except Exception, ex:
                    logging.exception("Exception copying file: %s to %s" % (src, dst))


def open_dir_with_explorer(files):
    # opens agents directory
    dirop = (config.basedir_av + "/" + os.path.dirname(files[0])).replace("/", "\\")
    cmd = 'cmd.exe /C start %s' % dirop
    logging.debug("Opening directory: %s" % dirop)
    subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    return dirop


def copy_files_extension(copy_extensions, files, files_to_check):
    # copy everything to .copy.exe, .copy.bat, .copy.com, .copy.dll
    for src in files:
        # logging.debug("DBG: check_static: %s" % src)
        for ext in copy_extensions:
            dst = "%s.copy.%s" % (src, ext)
            files_to_check.add(dst)
            if os.path.exists(src) and not os.path.exists(dst):
                logging.debug("Copying %s to %s" % (src, dst))
                try:
                    shutil.copy(src, dst)
                except Exception, ex:
                    logging.exception("Exception copying file: %s" % src)


def launch_static_scan(scan_dir, vm):
    try:
        antivirus = AV(vm)
        if antivirus.scan_cmd:
            cmd = antivirus.scan_cmd_replaced(scan_dir)
            logging.debug("Starting AV scan on directory: %s" % scan_dir)
            logging.debug("Command: %s" % cmd)
            #shell was true (shell=True,) but it does not work with
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            #i don;t think thi is all that thread safe...
            timer = threading.Timer(90.0, p.kill)
            #waits for AV scan end
            timer.start()
            out, err = p.communicate()
            print "Scan finished or scan timeout"
            timer.cancel()
            logging.debug("AV scan Finished. Result stdout: %s" % out)
            logging.debug("AV scan Finished. Result stderr: %s" % err)
        else:
            logging.debug("No 'scan_cmd' info found for av configuration: %s" % vm)
        return True
    except UndefinedAV:
        logging.debug("No AV configuration found for vm: %s" % vm)
        return False


#check static copies all the files in various manners supposing the files are already there.
#it continues to the end, because it need to ensure all detected files are reported
#but if all the files were detected by av it could be terminated to
def check_static_scan(files, vm, report=None):
    global report_send
    if report:
        report_send = report

    success = []
    failed = []
    copy_extensions = ['exe']  # , 'bat', 'com', 'dll']

    files_to_check = set()
    files_to_check.update(files)

    # for retrocompatibility, we add an agent.exe if it is not present. This is not added to the current list of files
    add_agent_exe(files, files_to_check)

    #opens explorer on this directory
    dirop = open_dir_with_explorer(files)

    #copy files from x.abc to x.abc.copy.exe
    copy_files_extension(copy_extensions, files, files_to_check)

    #launches av scan if configured in av yaml
    logging.debug("INITIATING SCAN!!!")
    logging.debug("INITIATING SCAN!!!")
    logging.debug("INITIATING SCAN!!!")
    logging.debug("INITIATING SCAN!!!")
    ret = launch_static_scan(dirop, vm)
    if not ret:
        failed = True

    sleep(60)
    #check file existance
    for to_check in files_to_check:
        if not os.path.exists(to_check):
            failed.append(to_check)
            logging.error("Not existent file (copy): %s" % to_check)
        else:
            success.append(to_check)
            logging.debug("Succesful static check of %s" % to_check)

    #in check_static there are other checks which proved not very effective and are not used in check_static_scan:
        # move files
        # read files

    #remove all. The files_to_check contains some files that exists no more (were renamed)
    #leave all originally extracted files (and agent.exe that sometimes is used)
    to_leave = ['agent.exe']
    for leave_me in files:
        to_leave.append(os.path.basename(leave_me))
    for rem_file in files_to_check:
        try:
            #leave all originally extracted files
            if os.path.basename(rem_file) not in to_leave:
                os.remove(rem_file)
                logging.debug("Removed %s" % rem_file)
        except Exception:
            pass

    if not failed:
        # failed is equal to []
        #does not add all checked files (it would be too verbose for a success!)
        add_result("+ SUCCESS CHECK_STATIC: %s" % files)
    else:
        add_result("+ FAILED CHECK_STATIC. SIGNATURE DETECTION: %s" % failed)
    logging.debug("Failed: %s" % failed)
    return failed


def check_static(files, report=None, scan=False, vm=None):

    global report_send
    if report:
        report_send = report

    rcs_words = ['rcs', 'hackingteam', 'hacking',
                 'zeno', 'guido', 'chiodo', 'naga', 'alor']
    success = []
    failed = []
    copy_extensions = ['exe', 'bat', 'com', 'dll']

    files_to_check = set()
    files_to_check.update(files)

    # for retrocompatibility, we add an agent.exe if it is not present. This is not added to the current list of files
    agent_exe_found = False
    for src in files:
        if src.endswith("\\agent.exe"):
            agent_exe_found = True
    if not agent_exe_found:
        for src in files:
            if os.path.exists(src) and str(src).endswith(".exe"):
                dst = os.path.join(os.path.dirname(src), "agent.exe")
                files_to_check.add(dst)
                logging.debug("Copying %s to %s" % (src, dst))
                try:
                    shutil.copy(src, dst)
                    break
                except Exception, ex:
                    logging.exception("Exception copying file: %s to %s" % (src, dst))

    #opens agents directory
    dirop = (config.basedir_av + "/" + os.path.dirname(files[0])).replace("/", "\\")
    cmd = 'cmd.exe /C start %s' % dirop
    logging.debug("Opening directory: %s" % dirop)
    subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

    #copy everything to .copy.exe, .copy.bat, .copy.com, .copy.dll
    for src in files:
        logging.debug("DBG: check_static: %s" % src)
        for ext in copy_extensions:
            dst = "%s.copy.%s" % (src, ext)
            files_to_check.add(dst)
            if os.path.exists(src) and not os.path.exists(dst):
                logging.debug("Copying %s to %s" % (src, dst))
                try:
                    shutil.copy(src, dst)
                except Exception, ex:
                    logging.exception("Exception copying file: %s" % src)
    sleep(30)
    if scan:
        logging.debug("1")
        ret = launch_static_scan(dirop, vm)
        if not ret:
            failed = True

    time.sleep(60)
    #check file existance after copy
    for to_check in files_to_check:

        if not os.path.exists(to_check):
            failed.append(to_check)
            logging.error("Not existent file (copy): %s" % to_check)
        else:
            success.append(to_check)
            logging.debug("Succesful static check of %s" % to_check)

    #renames all the 'copy' files to 'move'
    renamed = []
    for to_rename in success:
        if 'copy' in to_rename:
            dst = to_rename.replace('copy', 'move')
            if os.path.exists(to_rename) and not os.path.exists(dst):
                try:
                    os.rename(to_rename, dst)
                    #success.append(dst)
                    renamed.append(dst)
                except Exception:
                    logging.exception("Exception renaming to file: %s" % dst)
                    failed.append(dst)
    time.sleep(60)
    #check rename
    for to_check in renamed:
        if not os.path.exists(to_check):
            failed.append(to_check)
            logging.error("Not existent file (rename): %s" % to_check)
        else:
            success.append(to_check)
            logging.debug("Succesful static check of %s" % to_check)

    #read files
    if not failed:
        logging.debug("Trying to read files.")
        for f in files:
            to_read = (config.basedir_av + "/" + f).replace("/", "\\")
            cmd = 'cmd.exe /C type %s > nul' % to_read
            logging.debug("Reading file: %s" % to_read)
            subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    #no check, this should trigger some popup

    #remove all. The files_to_check contains some files that exists no more (were renamed)
    files_to_check.update(renamed)
    #leave all originally extracted files (and agent.exe that sometimes is used)
    to_leave = ['agent.exe']
    for leave_me in files:
        to_leave.append(os.path.basename(leave_me))
    for rem_file in files_to_check:
        try:
            #leave all originally extracted files
            if os.path.basename(rem_file) not in to_leave:
                os.remove(rem_file)
                logging.debug("Removed %s" % rem_file)
        except Exception:
            pass

    #old stuff that continue to be in place and working
    allowed = { 'rcs': ['AVAgent/assets/check/mac_core', 'AVAgent/assets/check/mac_osax'] }
    for src in files:
        if not os.path.exists(src):
            continue
        f = open(src)
        all = f.read()
        for key in rcs_words:
            allow_list = allowed.get(key, [])
            if key in allow_list:
                continue
            if key in all or key.lower() in all or key.upper() in all:
                #failed.append("Key: %s in %s" % (key, src))
                add_result("+ WARNING: %s in %s" % (key, src))

    if not failed:
        # failed is eual to []
        #does not add all checked files (it would be too verbose for a success!)
        add_result("+ SUCCESS CHECK_STATIC: %s" % files)
    else:
        add_result("+ FAILED CHECK_STATIC. SIGNATURE DETECTION: %s" % failed)
    logging.debug("Failed: %s" % failed)
    return failed


def internet_on():
    ips = ['173.194.35.176', '8.8.8.8', '8.8.4.4',
           '198.41.209.140', '204.79.197.200']
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


def get_target_name(build_server=False, puppet="avmaster"):
    if build_server:
        return 'VM_%s' % puppet
    else:
        return 'VM_%s' % helper.get_hostname()


def terminate_every_agent():
    logging.debug("Killing every agent...T1000 mode")
    for name in names:
        name_exe = name + ".exe"
        logging.debug(" - killing agent %s" % name_exe)
        os.system("taskkill /F /T /IM %s" % name_exe)


class AgentBuild:
    def __init__(self, backend, frontend=None, platform='windows', kind='silent',
                 ftype='desktop', blacklist=[], soldierlist=[], param=None,
                 puppet="puppet", asset_dir="AVAgent/assets", factory=None, server_side=False, final_action="unknown", zipfilename="", vm=None):
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
        self.server_side = server_side
        self.final_action = final_action
        self.zipfilename = zipfilename
        #needed by server side to clean evidences
        self.vm = vm
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
            timestr1 = time.strftime("%y%m%d-%H%M%S", time.localtime(time.time()))
            logging.debug("### Now launching %s with Popen - time: %s" % (exefile, timestr1))
            subp = subprocess.Popen(exefile, shell=True)
            timestr2 = time.strftime("%y%m%d-%H%M%S", time.localtime(time.time()))
            logging.debug("### Completed launching %s with Popen - time: %s" % (exefile, timestr2))

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
        res, log = util_agent.trigger_worked(logging)
        if not res:
            add_result(log)

    def _trigger_sync(self, timeout=10):
        subp = subprocess.Popen(['AVAgent/assets/keyinject.exe'])
        process.wait_timeout(subp, timeout)
        res, log = util_agent.trigger_worked(logging)
        if not res:
            add_result(log)
        # try:
        #     p = subprocess.Popen(['AVAgent/assets/getusertime.exe'], stdout=subprocess.PIPE)
        #     out, err = p.communicate()
        #     logging.debug("get usertime: %s" % out)
        # except:
        #     logging.exception("cannot get usertime")

    def get_can_upgrade(self, instance_id):
        with build_common.connection() as c:
            logging.debug("instance %s - getting get_can_upgrade level" % instance_id)
            level = str(c.instance_can_upgrade(instance_id))
            logging.debug("get_can_upgrade level: %s" % level)
            return level

    def check_level(self, instance, expected, set_result=True):
        with build_common.connection() as c:
            level = str(c.instance_level(instance))
            logging.debug("level, expected: %s got: %s" % (expected, level))
            if not level == expected:
                if set_result:
                    add_result("+ FAILED EXPECTED LEVEL: %s BUT GOT LEVEL: %s" % (expected.upper(), level.upper()))
                self.terminate_every_agent()
                executed = self.execute_agent_startup()
                return False
            else:
                if set_result:
                    add_result("+ SUCCESS %s LEVEL" % level.upper())
                return True

    def check_instance(self, ident, device=None):
        with build_common.connection() as c:

            if device is None:
                instances_id = c.instances(ident)
                logging.debug("DBG instances_id: %s" % instances_id)
            else:
                instances_id = c.instances_by_deviceid_and_ident(device, ident)
                logging.debug("DBG instances_id: %s - device: %s, ident:%s" % (instances_id, device, ident))

            #logging.debug("DBG rcs: %s" % str(build_common.connection.rcs))

            #assert len(instances) <= 1, "too many instances"

            if len(instances_id) == 1:
                add_result("+ SUCCESS SCOUT SYNC")
                c.instance = instances_id[0]
                return instances_id[0]
            elif len(instances_id) > 1:
                add_result("+ FAILED SCOUT SYNC, TOO MANY INSTANCES")
                c.instance = instances_id[0]
                return instances_id[0]

            add_result("+ NO SCOUT SYNC")
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
                add_result("+ SUCCESS UPGRADED SYNC (upgrade command received)")
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

    def create_user_machine(self, user_name = None):
        logging.debug("create_user_machine")
        return create_user(self.prefix, self.hostname)

    def execute_elite(self):
        """ build scout and upgrade it to elite """
        instance_id = self.execute_scout()
        self.execute_elite_fast(instance_id, False)

    def execute_soldier(self, instance_id = None, fast = True):
        instance_id = self.execute_scout()
        self.execute_soldier_fast(instance_id, False)

    def terminate_every_agent(self):
        logging.debug("Killing every agent...T1000 mode")
        for name in names:
            name_exe = name + ".exe"
            logging.debug(" - killing agent %s" % name_exe)
            os.system("taskkill /F /T /IM %s" % name_exe)

    def execute_soldier_fast(self, instance_id = None, fast = True):

        logging.debug("- instance_id: %s" % instance_id)

        if not instance_id:
            logging.debug("No instance_id, so I'll get it from connection")
            with build_common.connection() as c:
                instance_id, target_id = get_instance(c, device=helper.get_hostname(), build_server=self.server_side, puppet=self.prefix)
            logging.debug("- instance_id: %s, target_id: %s" % (instance_id, target_id))

        if not instance_id:
            add_result("+ FAILED NO INSTANCE_ID")
            return

        level = self.get_can_upgrade(instance_id)
        if level not in ["elite", "soldier"]:
            if self.hostname in self.blacklist:
                add_result("+ SUCCESS BLACKLIST: %s" % level)
            else:
                add_result("+ FAILED CANUPGRADE: %s" % level)
            return

        logging.debug("- Try upgrade to soldier")
        upgradable = self._upgrade(instance_id, force_soldier=True)
        if not upgradable:
            if self.hostname in self.blacklist:
                add_result("+ FAILED UPGRADE BLACKLISTED")
            else:
                if level == "Error409":
                    add_result("+ FAILED CANUPGRADE, NO DEVICE EVIDENCE")
                else:
                    add_result("+ FAILED CANUPGRADE: %s" % level)
            return
        else:
            logging.debug("upgraded correctly")

        return self.check_upgraded(instance_id, "soldier", fast)

    def execute_elite_fast(self, instance_id = None, fast = True):
    # GETTING THE INSTANCE ID
        logging.debug("- instance_id: %s" % instance_id)

        if not instance_id:
            logging.debug("No instance_id, so I'll get it from connection")
            with build_common.connection() as c:
                instance_id, target_id = get_instance(c, device=helper.get_hostname(), build_server=self.server_side, puppet=self.prefix)
                logging.debug("- instance_id: %s, target_id: %s" % (instance_id or 'NO_INSTANCE', target_id or 'NO_TARGET'))
        if not instance_id:
            add_result("+ FAILED NO INSTANCE_ID")
            logging.debug("- exiting execute_elite_fast because did't sync")
            return

    # CHECKING TO WHICH LEVEL I CAN UPGRADE
        level = self.get_can_upgrade(instance_id)
        if level == 'Error409' and self.hostname in self.soldierlist and self.platform == "windows_demo":
            add_result("+ SUCCESS DEMO SCOUT CANNOT BE UPGRADED TO SOLDIER AND VM IS IN SOLDIERLIST")
            logging.debug("- Uninstalling and closing instance: %s" % instance_id)
            self.uninstall(instance_id)
            #sleep(300)
            return
        if level in ["elite", "soldier"]:
            if self.hostname in self.blacklist:
                add_result("+ FAILED ALLOW BLACKLISTED (The av is in blacklist but I can upgrade)")
                logging.debug("- Uninstalling and closing instance: %s" % instance_id)
                self.uninstall(instance_id)
                return
        else: #error
            if self.hostname in self.blacklist:
                add_result("+ SUCCESS UPGRADE BLACKLISTED (The av is in blacklist and I cannot upgrade)")
            else:
                if level == "Error409":
                    add_result("+ FAILED CANUPGRADE, NO DEVICE EVIDENCE (or other server error. Maybe antivm were not disabled.)")
                else:
                    add_result("+ FAILED CANUPGRADE. Can_upgrade gave me this level: %s" % level)
            logging.debug("- Uninstalling and closing instance: %s" % instance_id)
            self.uninstall(instance_id)
            return

        logging.debug("- Try upgrade to %s" % level)
        upgradable = self._upgrade(instance_id)
        if not upgradable:
            add_result("+ FAILED UPGRADE")
            logging.debug("- Uninstalling and closing instance: %s" % instance_id)
            self.uninstall(instance_id)
            return

        logging.debug("DBG %s in %s and %s" % (self.hostname, self.blacklist, self.soldierlist))

        if level == "soldier":
            if self.hostname in self.soldierlist:
                add_result("+ SUCCESS SOLDIER BLACKLISTED (I'm doing an elite test but because the av is in soldierlist, I got a soldier update)")
            else:
                add_result("+ FAILED ELITE UPGRADE (maybe server says this vm is soldier, but rite thinks it's elite)")

            logging.debug("- Uninstalling and closing instance: %s" % instance_id)
            self.uninstall(instance_id)
            #sleep(300)
            return
        else:
            if self.hostname in self.soldierlist:
                add_result("+ FAILED SOLDIER BLACKLISTED (I'm doing an elite test and the av is in soldierlist but I haven't got a soldier level)")
                logging.debug("- Uninstalling and closing instance: %s" % instance_id)
                self.uninstall(instance_id)
                #sleep(300)
                return

        return self.check_upgraded(instance_id, level, fast)

    def check_upgraded(self, instance_id, level, fast=True):
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
                else:
                    if got_level.upper() == "SOLDIER":
                        self.terminate_every_agent()
                        executed = self.execute_agent_startup()
                for i in range(10):
                    self._click_mouse(100 + i, 0)

        else:
            logging.debug("- %s, Wait for 25 minutes: %s" % (level, time.ctime()))
            sleep(25 * 60)
            upgraded = self.check_level(instance_id, level)

        logging.debug("Upgraded: %s" % upgraded)
        if upgraded:
            logging.debug("The upgrade command was received, now the agent should sync.")
            #if got_level != level:
            #    add_result("+ FAILED LEVEL: %s" % level)
            sleep(60)
            #add_result("+ SUCCESS UPGRADE INSTALL %s" % got_level.upper())
            if level == "soldier":
                #                self.terminate_every_agent()
                executed = self.execute_agent_startup()
                if not executed:
                    add_result("+ FAILED EXECUTE %s" % level.upper())
                    upgraded = False
                else:
                    for tries in range(1, 10):
                        sleep(30)
                        self._trigger_sync(timeout=30)
                        for i in range(10):
                            self._click_mouse(100 + i, 0)

                        upgraded = self.check_level(instance_id, "soldier", set_result=False)
                        if upgraded:
                            add_result("+ SUCCESS %s LEVEL" % level.upper())
                            break
                    if not upgraded:
                        add_result("+ FAILED UPGRADE %s" % level.upper())
                        self.terminate_every_agent()
                        executed = self.execute_agent_startup()

            else:
                upgraded = self.check_level(instance_id, "elite")

            logging.debug("re executing scout")
            self._execute_build(["build/%s/agent.exe" % self.platform], silent=True)

            sleep(5 * 60)
            logging.debug("- %s, uninstall: %s" % (level, time.ctime()))
            #sleep(60)
            # self.uninstall(instance_id)
            sleep(60)
            if upgraded:
                add_result("+ SUCCESS %s UPGRADED, closing" % level.upper())
        else:
            output = self._list_processes()
            logging.debug(output)
            add_result("+ FAILED %s INSTALL" % level.upper())
        #added because kis detects the elite after some time.
        sleep(300)
        logging.debug("- Uninstalling and closing instance: %s" % instance_id)
        self.uninstall(instance_id)

        logging.debug("- Result: %s" % upgraded)
        logging.debug("- sending Results to Master")

    def execute_agent_startup(self):
        logging.debug("execute_agent_startup")
        executed = False

        """
        OLD AND AINT WORK WELL
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
        """
        for d in start_dirs:
            fz = glob.glob("%s%s*exe" % (d, os.sep))
            if fz is not None and fz != []:
                fz.sort(key=os.path.getmtime)
                filename = fz[-1]
                logging.debug("check if file exists: %s" % filename)
                if os.path.exists(filename):
                    logging.debug("try to execute: %s" % filename)
                    try:
                        subprocess.Popen([filename])
                        executed = True
                    except WindowsError:
                        logging.debug("%s is not a windows application. This is a detetion." % filename)
                        add_result("+ FAILED EXECUTION - the executable '%s' is not recognized by windows." % filename)
                        executed = False
                    break

        if not executed:
            for dir in start_dirs:
                dir = dir.replace("/", "\\")
                if os.path.exists(dir):
                    logging.debug("dir %s: %s" % (dir, os.listdir(dir)))
        return executed

    def execute_scout(self):
        #if is an elite demo but AV is SOLDIER, I need to exit, 'cause it will fail anyway!
        # (I need to exit BEFORE the static check (execute_pull)
        if self.final_action and self.final_action == "elite_fast_demo" and \
                (self.hostname in self.blacklist or self.hostname in self.soldierlist):
            add_result("+ SUCCESS ELITEDEMO on AV in Soldierlist or Blacklist - not executed and marked as passed")
            return None

        """ build and execute the  """
        factory_id, ident, exe = self.execute_pull()

        if type(exe) is list:
            if len(exe) == 0:
                return None
            exe = exe[0]

        logging.debug("execute_scout: %s" % exe)

        self._execute_build(exe)
        if self.kind == "melt":  # and not exploit
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

            #logging.debug("- self.server_side: %s" % self.server_side)
            if self.server_side:
                instance_id = self.check_instance(ident, device=helper.get_full_hostname())
            else:
                instance_id = self.check_instance(ident)
            if instance_id:
                break

            for i in range(10):
                self._click_mouse(100 + i, 0)

        if not instance_id:
            add_result("+ FAILED SCOUT SYNC")
            output = self._list_processes()
            logging.debug(output)
            return None
        else:
            if self.final_action and self.final_action == "elite_fast_demo":
                #DEMO ELITE MODE!!!
                self.check_level(instance_id, "elite")
                self.uninstall(instance_id)
            else:
                self.check_level(instance_id, "scout")
                if self.kind == "melt":
                    try:
                        found = False
                        for d, b in itertools.product(start_dirs, names):
                            filename = "%s/%s.exe" % (d, b)
                            filename = filename.replace("/", "\\")
                            if os.path.exists(filename):
                                found = True

                        if not found:
                            logging.warn("did'n executed")
                            add_result("+ FAILED NO STARTUP")
                    except:
                        pass

                if self.kind == "melt":
                    logging.debug("- melt, uninstall: %s" % (time.ctime()))
                    #sleep(60)
                    self.uninstall(instance_id)
                #already checked!
                #self.check_level(instance_id, "scout")
        logging.debug("- Result: %s" % instance_id)
        return instance_id

    #this is executed  ONLY when the build IS NOT A BUILD_SRV
    def execute_pull_client(self):
        """ build and execute the build without extraction and static check """

        logging.debug("- Host: %s %s\n" % (self.hostname, time.ctime()))
        # operation = build_common.connection.operation
        operation = "AOP_%s" % self.prefix #prefix e' uguale a puppet
        target = get_target_name()
        if not self.factory:
            factory = '%s_%s_%s_%s_%s' % (
                self.hostname, self.ftype, self.platform, self.kind, self.final_action)
        else:
            factory = self.factory

        config = "%s/config_%s.json" % (self.asset_dir, self.ftype)

        if not os.path.exists('build'):
            os.mkdir('build')
        if not os.path.exists('build/%s' % self.platform):
            os.mkdir('build/%s' % self.platform)

        #creates the factory
        #                                           create_new_factory(ftype, frontend, backend, operation, target, factory, config)
        target_id, factory_id, ident = build_common.create_new_factory(self.ftype, self.host[1], self.host[0], operation, target, factory, config)

        build_common.connection.rcs=(target_id, factory_id, ident, operation, target, factory)

        logging.debug("- Built, rcs: %s" % str(build_common.connection.rcs))

        meltfile = self.param.get('meltfile', None)

        zipfilename = 'build/%s/build.zip' % self.platform
        build_common.build_agent(factory_id, self.hostname, self.param, add_result, zipfilename, melt=meltfile, kind=self.kind)
        return factory_id, ident, zipfilename

    def _execute_extraction_and_static_check(self, zipfilename):
        #ML qui sono state messe le parti di check statica
        if os.path.exists(zipfilename):
            exefilenames = unzip(zipfilename, "build/%s" % self.platform)
        else:
            logging.debug("cannot find zip file: %s" % zipfilename)
            add_result("+ FAILED SCOUT BUILD. CANNOT FIND ZIP FILE %s TO UNZIP IT" % zipfilename)
            # raise RuntimeError("No file to unzip")
            #returns empty list
            return []
        # CHECK FOR DELETED FILES
        failed = check_static(exefilenames)

        if not failed:
            add_result("+ SUCCESS SCOUT BUILD (no signature detection)")
        else:
            add_result("+ FAILED SCOUT BUILD. SIGNATURE DETECTION: %s" % failed)
            # raise RuntimeError("Signature detection")
            logging.debug("FAILED STATIC. Signature detection: %s" % failed)
            #returns empty list
            return []

        return exefilenames

    #substituted self.vm with helper.get_full_hostname()
    def clean_previous_instances(self, factory_id):
        logging.debug("- I'm gonna clean instances for factory_id: %s and device: %s" % (factory_id, helper.get_full_hostname()))

        with build_common.connection() as c:
            num_instances_deleted = 0
            #TODO chck if factory_id is ok and vm is ok for device
            instances_to_clean = c.instances_by_factory(helper.get_full_hostname(), factory_id)
            logging.debug("- found %s instances to be deleted: %s" % (len(instances_to_clean), instances_to_clean))
            for instance in instances_to_clean:
                c.instance_delete(instance_id=instance['_id'])
                num_instances_deleted += 1
            logging.debug("- %s instances deleted" % num_instances_deleted)
            return num_instances_deleted

    def execute_pull(self):
        """ build and execute the  """
        if self.server_side:
            # logging.debug("factory = %s" % self.factory)
            target_id, factory_id, ident = self.factory

            #here I must delete the previous targets, but only if this is the frist step of th build
            #(for example, in case of elite, only in the "scout" execution)
            self.clean_previous_instances(ident)

            exe = self._execute_extraction_and_static_check(self.zipfilename)
        else:
            factory_id, ident, zipfilename = self.execute_pull_client()
            exe = self._execute_extraction_and_static_check(zipfilename)

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
    filename = ""
    ftype = args.platform_type
    logging.debug("DBG ftype: %s" % ftype)

    if args.server_side:
        vmavtest = AgentBuild(args.backend, frontend=args.frontend,
                        platform=platform, kind=args.kind, ftype=ftype, blacklist=args.blacklist,
                        soldierlist=args.soldierlist, param=args.param, puppet=args.puppet, asset_dir=args.asset_dir,
                        factory=args.factory, server_side=args.server_side, final_action=args.final_action, zipfilename=args.exe, vm=args.vm)
    else:
        vmavtest = AgentBuild(args.backend, frontend=args.frontend,
                        platform=platform, kind=args.kind, ftype=ftype, blacklist=args.blacklist,
                        soldierlist=args.soldierlist, param=args.param, puppet=args.puppet, asset_dir=args.asset_dir,
                        factory=args.factory, server_side=args.server_side)

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
            #deleted: "pull_server": vmavtest.execute_pull_client,
            # 'elite_fast_demo' and 'soldier_fast_demo' are not actions, are FINAL_actions
            # so i deleted "elite_fast_demo": vmavtest.execute_elite_fast_demo, "soldier_fast_demo": vmavtest.execute_soldier_fast_demo
            action = {"elite": vmavtest.execute_elite, "scout": vmavtest.execute_scout,
                      "pull": vmavtest.execute_pull, "elite_fast": vmavtest.execute_elite_fast,
                      "soldier_fast": vmavtest.execute_soldier_fast, "soldier": vmavtest.execute_soldier}
            sleep(5)
            action[level]()

        else:
            add_result("+ ERROR USER CREATE")

    return True


def get_instance(client, device=None, build_server=False, puppet=None):
    print 'passed imei to get_isntance ', device
    #logging.debug("client: %s" % client)
    operation_id, group_id = client.operation(build_common.connection.operation)

    if build_server:
        target = get_target_name(build_server=build_server, puppet=puppet)
    else:
        target = get_target_name()

    targets = client.targets(operation_id, target)

    if len(targets) != 1:
        return False, "not one target: %s, target name: %s, operation_id: %s, group_id:%s, operation name: %s" % (len(targets), target, operation_id, group_id, build_common.connection.operation)

    target_id = targets[0]
    instances = client.instances_by_target_id(target_id)
    instances = [k for k in instances if k['status'] == 'open']

    logging.debug("found these instances: %s" % instances)
    if len(instances) == 0:
        return False, "no open instances"

    if not device:
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
            instance = [inst for inst in instances if inst["stat"]['device'].lower().endswith(device.lower())][0]
        except:
            logging.debug("No instance found for device: %s - Returning None, None" % device)
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

        #instance_id, target_id = get_instance(c, self.server_side, self.prefix, device=helper.get_hostname())
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

def check_blacklist(blacklist=None):
    with build_common.connection() as client:
        logging.debug("connected")
        blacklist_server = client.blacklist()
        logging.info("blacklist from server: %s" % blacklist_server)
        if blacklist:
            logging.info("blacklist from conf: %s" % blacklist)
        report_send("+ BLACKLIST: %s" % blacklist_server)


def create_user(puppet, vm, backend=None):
    if backend:
        build_common.connection.host = backend
    logging.debug("create_user %s, %s" % (puppet, vm))
    user_name = "avmonitor_%s_%s" % (puppet, vm)
    build_common.connection.user = user_name

    user_exists = False
    try:
        with build_common.connection() as c:
            logging.debug("LOGIN SUCCESS")
            user_exists = True
    except:
        pass

    if not user_exists:
        privs = [
            'ADMIN', 'ADMIN_USERS', 'ADMIN_OPERATIONS', 'ADMIN_TARGETS', 'ADMIN_AUDIT',
            'ADMIN_LICENSE', 'SYS', 'SYS_FRONTEND', 'SYS_BACKEND', 'SYS_BACKUP',
            'SYS_INJECTORS', 'SYS_CONNECTORS', 'TECH',
            'TECH_FACTORIES', 'TECH_BUILD', 'TECH_CONFIG', 'TECH_EXEC', 'TECH_UPLOAD',
            'TECH_IMPORT', 'TECH_NI_RULES', 'VIEW', 'VIEW_ALERTS', 'VIEW_FILESYSTEM',
            'VIEW_EDIT', 'VIEW_DELETE', 'VIEW_EXPORT', 'VIEW_PROFILES']

        build_common.connection.user = "avmonitor"
        with build_common.connection() as c:
            ret = c.operation(build_common.connection.operation)
            op_id, group_id = ret
            c.user_create(user_name, build_common.connection.passwd, privs, group_id)
    build_common.connection.user = user_name
    return True

def uninstall(backend):
    logging.debug("- Clean Server: %s" % (backend))
    build_common.connection.host = backend

    target = get_target_name()
    logging.debug("target: %s" % target)

    with build_common.connection() as client:
        logging.debug("connected")

        operation_id, group_id = client.operation(build_common.connection.operation)
        targets = client.targets(operation_id, target)
        if len(targets) != 1:
            return False, "not one target: %s" % len(targets)

        target_id = targets[0]
        #instances = client.instances_by_target_id(target_id)
        instances = client.instances_by_deviceid_and_ident(target_id, device=helper.get_full_hostname())

        logging.debug("found these instances: %s" % instances)
        if len(instances) != 1:
            logging.warn("more than one instance")

        for instance in instances:
            instance_id = instance['_id']
            target_id = instance['path'][1]
            logging.debug('closing instance: %s' % instance)
            client.instance_close(instance_id)
        return True, "Instance closed"

# def clean_factories_and_instances(backend):
#     logging.debug("- Clean Server: %s" % (backend))
#     build_common.connection.host = backend
#
#     target = get_target_name()
#     logging.debug("target: %s" % target)
#
#     with build_common.connection() as client:
#         logging.debug("connected")
#
#         operation_id, group_id = client.operation(build_common.connection.operation)
#         targets = client.targets(operation_id, target)
#         if len(targets) != 1:
#             return False, "not one target: %s" % len(targets)
#
#         target_id = targets[0]
#         instances = client.instances_by_deviceid_and_ident(target_id, device=helper.get_full_hostname())
#
#         logging.debug("found these instances: %s" % instances)
#         ins_num = 0
#         for instance in instances:
#             instance_id = instance['_id']
#             target_id = instance['path'][1]
#             logging.debug('deleting instance: %s' % instance)
#             client.instance_delete(instance_id)
#             ins_num += 1
#
#         fac_num = 0
#             client.fac
#
#
#
#         return (fac_num, ins_num)


def clean(backend, puppet):
    operation = "AOP_" + puppet
    logging.debug("- Clean Server: %s - Operation: %s" % (backend, operation))
    build_common.connection.host = backend
    vmavtest = AgentBuild(backend, puppet=puppet)
    return vmavtest._delete_targets(operation)


def disable_analysis(backend):
    logging.debug("- Disable Analysis: %s" % (backend))
    build_common.connection.host = backend
    vmavtest = AgentBuild(backend)
    return vmavtest._disable_analysis()


def build(args, report):
    global results, report_send
    results = []

    report_send = report
    filename = ""
    build_common.connection.host = args.backend
    build_common.connection.operation = args.operation

    action = args.action
    platform = args.platform
    kind = args.kind

    if report_send:
        report_send("+ INIT %s, %s, %s" % (action, platform, kind))

    try:
        #check_blacklist(blacklist)
        # 'elite_fast_demo' is not an action, is a FINAL_action (because it uses a scout).
        # 'elite_fast_scoutdemo' is an action (also a FINAL_action) because it hase a second step
        if action in ["pull", "scout", "elite", "elite_fast", "soldier", "soldier_fast", "elite_fast_scoutdemo"]:
            success_ret = execute_agent(args, action, args.platform)
        #probably doesn't works because the backend is not the right parameter
        elif action == "clean":
            clean(args.backend, args.puppet)
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


# def main():
#     parser = argparse.ArgumentParser(description='AVMonitor avtest.')
#
#     #'elite'
#     parser.add_argument(
#         'action', choices=['scout', 'elite', 'internet', 'test', 'clean', 'pull'])
#     parser.add_argument('-p', '--platform', default='windows')
#     parser.add_argument('-b', '--backend')
#     parser.add_argument('-f', '--frontend')
#     parser.add_argument('-k', '--kind', choices=['silent', 'melt'])
#     parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Verbose")
#
#     #parser.set_defaults(blacklist=blacklist)
#     #parser.set_defaults(platform_type=platform_type)
#
#     args = parser.parse_args()
#
#     #edit by ML
#     winhostname = socket.gethostname().lower()
#
#     if "winxp" in winhostname:
#         avname = winhostname.replace("winxp", "").lower()
#     elif "win7" in winhostname:
#         avname = winhostname.replace("win7", "").lower()
#     else:
#         avname = winhostname.replace("win8", "").lower()
#
#     platform_mobile = ["android", "blackberry", "ios"]
#
#
#     soldierlist = "adaware,iobit32,bitdef,bitdef15,comodo,fsecure,gdata,drweb,360cn5,kis32,avg,avg32,norman,avira,avira15".split(',')
#     #OLD
#     #soldierlist = "bitdef,comodo,gdata,drweb,360cn,kis32,avg,avg32,iobit32".split(',')
#     blacklist = "emsisoft,sophos,kis32".split(',')
#     demo = False
#
#     params = {}
#     params['blackberry'] = {
#         'platform': 'blackberry',
#         'binary': {'demo': demo},
#         'melt': {'appname': 'facebook',
#                  'name': 'Facebook Application',
#                  'desc': 'Applicazione utilissima di social network',
#                  'vendor': 'face inc',
#                  'version': '1.2.3'},
#         'package': {'type': 'local'}}
#     params['windows'] = {
#         'platform': 'windows',
#         'binary': {'demo': demo, 'admin': False},
#         'melt': {'scout': True, 'admin': False, 'bit64': True, 'codec': True},
#         'sign': {}
#     }
#     params['android'] = {
#         'platform': 'android',
#         'binary': {'demo': demo, 'admin': False},
#         'sign': {},
#         'melt': {}
#     }
#     params['linux'] = {
#         'platform': 'linux',
#         'binary': {'demo': demo, 'admin': False},
#         'melt': {}
#     }
#     params['osx'] = {'platform': 'osx',
#                      'binary': {'demo': demo, 'admin': True},
#                      'melt': {}
#     }
#     params['ios'] = {'platform': 'ios',
#                      'binary': {'demo': demo},
#                      'melt': {}
#     }
#
#     params['exploit'] = {"generate":
#                              {"platforms": ["windows"], "binary": {"demo": False, "admin": False},
#                               "exploit": "HT-2012-001",
#                               "melt": {"demo": False, "scout": True, "admin": False}}, "platform": "exploit",
#                          "deliver": {"user": "USERID"},
#                          "melt": {"combo": "txt", "filename": "example.txt", "appname": "agent.exe",
#                                   "input": "000"}, "factory": {"_id": "000"}
#     }
#
#     params['exploit_docx'] = {"generate":
#                                   {"platforms": ["windows"], "binary": {"demo": False, "admin": False},
#                                    "exploit": "HT-2013-002",
#                                    "melt": {"demo": False, "scout": True, "admin": False}},
#                               "platform": "exploit", "deliver": {"user": "USERID"},
#                               "melt": {"filename": "example.docx", "appname": "APPNAME", "input": "000",
#                                        "url": "http://HOSTNAME/APPNAME"}, "factory": {"_id": "000"}
#     }
#     params['exploit_ppsx'] = {"generate":
#                                   {"platforms": ["windows"], "binary": {"demo": False, "admin": False},
#                                    "exploit": "HT-2013-003",
#                                    "melt": {"demo": False, "scout": True, "admin": False}},
#                               "platform": "exploit", "deliver": {"user": "USERID"},
#                               "melt": {"filename": "example.ppsx", "appname": "APPNAME", "input": "000",
#                                        "url": "http://HOSTNAME/APPNAME"}, "factory": {"_id": "000"}
#     }
#     params['exploit_web'] = {"generate":
#                                  {"platforms": ["windows"], "binary": {"demo": False, "admin": False},
#                                   "exploit": "HT-2013-002",
#                                   "melt": {"demo": False, "scout": True, "admin": False}},
#                              "platform": "exploit", "deliver": {"user": "USERID"},
#                              "melt": {"filename": "example.docx", "appname": "APPNAME", "input": "000",
#                                       "url": "http://HOSTNAME/APPNAME"}, "factory": {"_id": "000"}
#     }
#
#     p_t = "desktop"
#     if args.platform in platform_mobile:
#         p_t = "mobile"
#     build(args.action, args.platform, p_t, args.kind,
#           params[args.platform], args.backend,
#           args.frontend, blacklist, soldierlist, None)
#
#
# if __name__ == "__main__":
#     main()
