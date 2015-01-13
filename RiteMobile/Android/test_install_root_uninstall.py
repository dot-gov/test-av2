# -*- coding: utf-8 -*-
import json

import time
import csv
import os
import traceback
import collections
import datetime
import argparse
import inspect
import sys
import signal
import subprocess

inspect_getfile = inspect.getfile(inspect.currentframe())
cmd_folder = os.path.split(os.path.realpath(os.path.abspath(inspect_getfile)))[0]
os.chdir(cmd_folder)

#print cmd_folder

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)
parent = os.path.split(cmd_folder)[0]
ancestor = os.path.split(parent)[0]
if parent not in sys.path:
    sys.path.insert(0, parent)
if ancestor not in sys.path:
    sys.path.insert(0, ancestor)

#print sys.path

from RiteMobile.Android.commands_device import CommandsDevice
from RiteMobile.Android.commands_rcs import CommandsRCSZeus as CommandsRCS

# apk_template = "build/android/install.%s.apk"
apk_template = "assets/autotest.%s.apk"
service = 'com.android.dvci'
apk_report = "assets/report.apk"""


def say(text):
    os.system("say " + text)


def check_disinfected(command_dev, results):
    still_infected = False
    if command_dev.check_infection():
        print "Manual uninstall required !!! Clean the phone !!!"
        return False
        #command_dev.uninstall_agent()

        still_infected = command_dev.check_infection()

    if still_infected:
        print "Error, still installed"
        return False

    results["packages_remained"] = still_infected
    return True


def install(command_dev, results):
    if results['release'].startswith("2"):
        agent = "agent_v2"
    else:
        agent = "agent"

    print "... installing %s" % agent
    # install
    if not command_dev.install(agent):
        return False

    results["installed"] = True
    print "installation: OK"
    return True


def check_evidences(command_dev, c, results, timestamp=""):
    print "... check_evidences"
    time.sleep(60)
    evidences, kinds = c.evidences()

    for k in ["call", "chat", "camera", "application", "mic"]:
        if k not in kinds.keys():
            kinds[k] = []

    ev = "\n"
    ok = kinds.keys()
    ok.sort()
    for k in ok:
        ev += "\t\t%s: %s\n" % (k, len(kinds[k]))
        if k in ["chat", "addressbook", "call"]:
            program = [e['data']['program'] for e in evidences if e['type'] == k]
            chat = set(program)
            for c in chat:
                ev += "\t\t\t%s\n" % (c)

    results['evidences' + timestamp] = ev
    results['evidence_types' + timestamp] = kinds.keys()

    results['uptime' + timestamp] = command_dev.get_uptime()

    expected = set()
    packages = command_dev.get_packages()
    for i in ['skype', 'facebook', 'wechat', 'telegram', 'hangout', 'android.talk', 'line.android', 'viber',
              'tencent.mm', 'whatsapp']:
        for p in packages:
            if i in p:
                expected.add(i)

    results['expected'] = list(expected)


def uninstall_agent_with_calc(commands_device, results, quick):
    if not commands_device.execute_calc():
        print "failed to run CALC!!!"

    if quick:
        time.sleep(5)
        return
    say("agent uninstall, verify request")
    if 'No' != results['root']:
        print "uninstall:without DIALOG"
        for i in range(12):
            time.sleep(10)
            processes = commands_device.get_processes()
            uninstall = service not in processes
            if uninstall:
                break
    else:
        print "uninstall:DIALOG !!!"
        uninstall = unistall_dialog_wait_and_press(commands_device, 120)

    print "uninstall: wait 30sec"
    time.sleep(30)
    results['uninstall'] = uninstall

    if not uninstall:
        print "uninstall: ERROR"
        print "processes: %s" % processes
        commands_device.uninstall_agent()
    else:
        print "uninstall: OK"


def check_uninstall(commands_device, results, reboot=True):
    if reboot:
        print ".... reboot"
        commands_device.reboot()
        time.sleep(60)

    processes = commands_device.get_processes()
    running = "still running: %s" % service in processes
    results['running'] = running

    res = commands_device.execute_cmd(
        "ls /sdcard/1 /sdcard/2 /system/bin/debuggered /system/bin/ddf /data/data/com.android.deviceinfo/ /data/data/com.android.dvci/ /sdcard/.lost.found /sdcard/.ext4_log /data/local/tmp/log /data/dalvik-cache/*StkDevice*  /data/dalvik-cache/*com.android.dvci* /data/app/com.android.dvci*.apk /system/app/StkDevice*.apk 2>/dev/null")
    results["files_remained"] = res

    # res = adb.executeSU('cat /data/system/packages.list  | grep -i -e "dvci" -e "deviceinfo" -e "StkDevice"')
    # res += adb.executeSU('cat /data/system/packages.xml  | grep -i -e "dvci" -e "device" -e "StkDevice"')
    res = commands_device.execute_cmd('pm path com.android.deviceinfo')
    res += commands_device.execute_cmd('pm path com.android.dvci')

    results["packages_remained"] = res


def check_skype(command_dev, c, results):
    supported = ['4.0', '4.1', '4.2', '4.3']
    release = results['release'][0:3]

    results['call_supported'] = release in supported
    if release not in supported:
        print "Call not supported"
        return

    # check if skype is installed
    if command_dev.check_remote_app_installed("skype", 5) != 1:
        print "skype not installed, skypping test"
        return

    print "... waiting for call inject"
    info_evidences = []
    counter = 0
    while not info_evidences and counter < 10:
        info_evidences = c.infos('Call')

        counter += 1
        if not info_evidences:
            print "... waiting for info"
            time.sleep(10)
        else:
            break

    for i in range(10):
        time.sleep(10)
        ret = command_dev.execute_root("ls /data/data/com.android.dvci/files/l4")
        print ret
        if "No such file" not in ret:
            print "Skype call and sleep"
            command_dev.skype_call()
            time.sleep(90)
            ret = command_dev.execute_root("ls /data/data/com.android.dvci/files/l4")
            print ret
            break


def check_camera(command_dev):
    command_dev.press_key_home()
    command_dev.execute_cmd("am start -a android.media.action.IMAGE_CAPTURE")
    time.sleep(5)
    command_dev.press_key_home()

def unistall_dialog_wait_and_press(command_dev,timeout=60):
    if not command_dev.check_remote_activity("UninstallerActivity", timeout):
        res = "process dvci still running\n"
        print res
        return "Fail"
    else:
        command_dev.press_key_enter()
        command_dev.press_key_tab()
        command_dev.press_key_enter()
        command_dev.press_key_home()
        time.sleep(4)
        return "Success"

def check_mic(command_dev):
    command_dev.press_key_home()
    #on contacts start mic
    command_dev.execute_cmd("am start com.android.contacts -n  com.android.contacts/.activities.DialtactsActivity -c android.intent.category.LAUNCHER")
    time.sleep(2)
    if command_dev.check_remote_process("com.android.contacts", 5) == -1:
        if command_dev.check_remote_process("ResolverActivity", 5) == -1:
            command_dev.press_key_enter()
        if command_dev.check_remote_process("com.android.contacts", 5) == -1:
            if command_dev.check_remote_process("ResolverActivity", 5) != -1:
                command_dev.press_key_enter()
                command_dev.press_key_enter()
                command_dev.press_key_tab()
                command_dev.press_key_tab()
                command_dev.press_key_enter()
    time.sleep(25)
    command_dev.press_key_home()

def set_properties(command_dev, results):
    # getprop device
    props = command_dev.get_properties()
    device = "%s %s" % (props["manufacturer"], props["model"])

    results['time'] = "%s" % datetime.datetime.now()
    results['device'] = device
    results['id'] = command_dev.get_dev_deviceid()
    results['usbId'] = command_dev.get_dev_serialno()
    results['release'] = props["release"]
    results['selinux'] = props["selinux"]
    results['build_date'] = props["build_date"]
    results['error'] = ""
    results['return'] = ""
    results['uninstall'] = ""
    results['persistency'] = "NO"
    return results


def check_format_resist(command_dev, c, results, delay=60):
    print "... check format_resist and reboot"
    command_dev.press_key_home()

    if not command_dev.execute_cmd("ls /system/app/StkDevice.apk"):
        results["format_resist"] = "No";
        return

    command_dev.reboot()
    time.sleep(delay)

    c.wait_for_start(2)

    command_dev.unlock_screen()

    ret = command_dev.execute_cmd("ls /system/app/StkDevice.apk")

    inst = command_dev.execute_cmd("pm path com.android.dvci")
    if "/data/app/" in inst:
        if "No such file" in ret:
            results["format_resist"] = "No";
        else:
            results["format_resist"] = "Reboot"
    elif "/system/app/" in inst:
        results["format_resist"] = "Yes";
        print "... got format_resist"
    else:
        results["format_resist"] = "Error";


def report_if_exists(results, param):
    report = ""
    for p in param:
        report += "\t%s: %s\n" % (p, results.get(p, ""))
    return report


def report_test_rail(results):
    report = ""
    report += "Installation\n"
    report += report_if_exists(results,
                               ["time", "installed", "executed", "instance_name", "info", "uptime_first", "uptime_last",
                                "error",
                                "exception"])
    report += "Device\n"
    report += report_if_exists(results, ["device", "id", "release", "build_date"])
    report += "Root\n"
    report += report_if_exists(results, ["root", "root_first", "su", "selinux", "format_resist"])
    report += "Evidences\n"
    report += report_if_exists(results, ["evidences_first", "evidences_last"])
    report += "Expected\n"
    report += report_if_exists(results, ["call_supported", "expected"])
    report += "Uninstall\n"
    report += report_if_exists(results, ["uninstall", "running", "files_remained", "packages_remained"])

    print report
    return report


def report_files(results, report):
    with open('report/test-%s.%s.txt' % (results.get('id', 0), results.get('device', "device")), 'ab') as tfile:
        tfile.write(report)

    with open('report/test-%s.%s.csv' % (results.get('id', 0), results.get('device', "device")), 'ab') as csvfile:
        # write header
        devicelist = csv.writer(csvfile, delimiter=";",
                                quotechar="|", quoting=csv.QUOTE_MINIMAL)
        devicelist.writerow(results.values())

    with open('logs/hardware.logs.txt', 'a+') as logfile:
        logfile.write(str(results))
        logfile.write("\n")

    with open('logs/hardware.logs.py', 'a+') as logfile:
        logfile.write("h.append(collections." + str(results) + ")")
        logfile.write("\n")


import threading

class LogcatThread(object):
    """ Threading example class

    The run() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, cmd, interval=1):
        """ Constructor

        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.interval = interval
        self.run_baby = True
        print "lunching thread with cmd=%s" % cmd
        self.pro = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                       shell=True, preexec_fn=os.setsid)
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        """ Method that runs forever """
        while self.run_baby:
            time.sleep(self.interval)
        os.killpg(self.pro.pid, signal.SIGTERM)


# The os.setsid() is passed in the argument preexec_fn so
# it's run after the fork() and before  exec() to run the shell.

def check_dir(dir):
    if not os.path.exists(dir):
        d = os.mkdir(dir)
    if os.path.exists(dir):
        return True
    return False


def set_status(command_dev, status):
    #def send_intent(self, package, activity, extras)

    extra = "result %s" % status.replace(" ","_")
    command_dev.send_intent("com.example.zad.report", ".ReportActivity", [extra])


def test_device(command_dev, args, results):

    if args.fastnet:
        command_dev.wifi('open', check_connection=False, install=True)
        return "open"

    if args.reboot:
        command_dev.reboot()

    # tests = ["sync","format_resist","root", "skype","camera"]
    # tests = ["format_resist"]


    if not os.path.exists(args.apk):
        printl("ERROR, cannot get apk")
        return "apk not found %s" % args.apk

    command_dev.set_auto_rotate_enabled(False)
    command_dev.unlock_screen()

    try:

        # install agent and check it's running
        # todo: to install the agent, it'e more secure to
        # unistall via "calc" and then use pm uninstall
        printl( "report tools apk %s" % apk_report)
        if os.path.exists(apk_report): # :
            if command_dev.is_package_installed("com.example.zad.report"):
                command_dev.uninstall_package("com.example.zad.report")
            proc = command_dev.install_apk_direct_th(apk_report)
            while proc.is_alive_inner():
                # some caseses android require confirmation to install via adb i.e. xianomi
                if command_dev.check_remote_activity("com.android.packageinstaller/.PackageInstallerActivity", 3):
                    command_dev.press_key_enter()
                    command_dev.press_key_tab()
                    command_dev.press_key_tab()
                    command_dev.press_key_enter()
        if check_disinfected(command_dev, results):
            printl( "installing apk %s" % args.apk)
            proc = command_dev.install_apk_direct_th(args.apk)
            # some caseses android require confirmation to install via adb i.e. xianomi
            while proc.is_alive_inner():
                if command_dev.check_remote_activity("com.android.packageinstaller/.PackageInstallerActivity", 3):
                    command_dev.press_key_enter()
                    command_dev.press_key_tab()
                    command_dev.press_key_tab()
                    command_dev.press_key_enter()
            if not command_dev.check_infection():
                set_status(command_dev, "INSTALLATION FAIL")
                printl("installation fail")
                printl(str(results))
                return "old installation fail"
        else:
            set_status(command_dev, "AGENT ALREDY PRESENT")
            printl("old installation present")
            printl(str(results))
            return "old installation present"
        zygote_pid = command_dev.check_remote_process("zygote", 10)
        printl("started zygote pid %d" % zygote_pid)
        printl("executing apk %s" % args.apk)
        results["executed"] = command_dev.execute_agent()
        if results["executed"]:
            printl("... executed")
            time.sleep(5)
        else:
            set_status(command_dev, "UNABLE TO RUN AGENT")
            printl(str(results))
            return "execution failed"
        agent_pid = command_dev.check_remote_process("com.android.dvci", 10)
        command_dev.press_key_home()
        time.sleep(5)
        printl( "check su")
        results["su"] = command_dev.info_root()
        tried = 0
        if not args.quick_uninstall:
            # check for root for 6 minutes at least
            while True:
                number = command_dev.check_number_remote_process("dvci", 6)
                printl( "check eploit running number=%d tried=%d" % (number, tried))
                if number < 2 or tried >= 6:
                    break
                else:
                    time.sleep(60)
                    tried += 1
            printl( "check local root...")

        root_result = command_dev.info_local_exploit()
        if root_result:
            results['root'] = "Yes"
            printl( results['root'])
            #try to force persistency agent restart
            command_dev.lock_and_unlock_screen();
            time.sleep(5)
            command_dev.lock_and_unlock_screen();
            time.sleep(5)
            command_dev.check_remote_process_change_pid("com.android.dvci", 30, agent_pid)
            if command_dev.check_remote_file_quick("/system/app/StkDevice*.apk"):
                printl( "persistency detected")
                results['persistency'] = "PRESENT"
                command_dev.lock_and_unlock_screen()
        else:
            results['root'] = "No"
            printl( results['root'])


        # uninstall
        command_dev.unlock_screen()
        printl( "uninstall via calc apk %s" % args.apk)
        uninstall_agent_with_calc(command_dev, results, args.quick_uninstall)

        if args.quick_uninstall:
            command_dev.press_key_home()
            double_check = 0
            if command_dev.check_remote_process_change_pid("zygote", 240, zygote_pid):
                double_check_limit = 3
            else:
                double_check_limit = 1
            while True:

                number = command_dev.check_number_remote_process("dvci", 6)
                printl( "check unistall running number=%d tried=%d dc=%d" % (number, tried,double_check))
                if number == 0 or tried >= 360:
                    if double_check > double_check_limit:
                        break
                    double_check += 1
                else:
                    command_dev.lock_and_unlock_screen()
                    if root_result:
                        time.sleep(10)
                    else:
                        unistall_dialog_wait_and_press(command_dev, 10)

                    tried += 1
                    if tried/3:
                        uninstall_agent_with_calc(command_dev, results, args.quick_uninstall)

        # check uninstall after reboot
        time.sleep(10)
        printl( "check uninstall apk %s" % args.apk)
        notinfected = check_disinfected(command_dev,results)
        if not notinfected:
            printl( "UNINSTALL FAILED")
            set_status(command_dev, "UNINSTALL FAILED")
            printl(str(results))
            return "UNINSTALL FAILED"

        printl("monitor zygote[%d] for 120 sec" % command_dev.check_remote_process("zygote", 10))
        results['zygote crashed'] = command_dev.check_remote_process_change_pid("zygote", 240, zygote_pid)
        printl("monitored zygote[%d] for 120 sec" % command_dev.check_remote_process("zygote", 10))
        if results['zygote crashed'] :
            printl( "zygote CRASHED !!!!!!")
            set_status(command_dev, "zygote CRASHED")
            printl(str(results))
            return  "zygote CRASHED !!!!!!"
        else:
            printl( "all ok")
            printl(str(results))
            set_status(command_dev, "TEST PASSED")
            return None

    except Exception, ex:
        traceback.print_exc()
        results['error'] = "%s" % ex
        return "Exception"


def parse_args():
    parser = argparse.ArgumentParser(description='run install and uninstall.')
    parser.add_argument('-a', '--apk', required=True,
                        help="apk to use")
    parser.add_argument('-d', '--device', required=False,
                        help="choose serial number of the device to use")
    parser.add_argument('-i', '--interactive', required=False, action='store_true',
                        help="Interactive execution")
    parser.add_argument('-f', '--fastnet', required=False, action='store_true',
                        help="Install fastnet")
    parser.add_argument('-n', '--number', required=False, type=int,
                        help="number of time to run the test")
    parser.add_argument('-r', '--reboot', required=False, action='store_true',
                        help="Install fastnet")
    parser.add_argument('-q', '--quick_uninstall', required=False, action='store_true',
                        help="unistall without waiting the root")
    parser.add_argument('-l', '--log', required=False, action='store_true',
                        help="enable logging")
    parser.add_argument('-v', '--logcat', required=False, action='store_true',
                        help="enable logcat logging")
    parser.add_argument('-A', '--all', required=False, action='store_true',
                        help="run all devices, just ignore here")


    args = parser.parse_args()
    return args


def printl(*s):
    print "%s" % s
    if main._file_logs and not main._file_logs.closed:
        main._file_logs.write("%s" % s)
        main._file_logs.write("\n")
        main._file_logs.flush()
    printlc("%s" % s)
    return True


def close_log_file():
    if main._file_logs and not main._file_logs.closed:
        main._file_logs.close
    return


def open_log_file(dir,prefix):
    st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H.%M')
    filename = dir+"/"+prefix+st+".log"
    print("opening file for log:%s" % filename)
    try:
        main._file_logs = open(filename, "wa")
    except IOError as err:
        print("unable to open file :%s %s" % (filename, err))
        main._file_logs = None
    return main._file_logs

def printlc(*s):
    if main._file_logcat :
        #main._file_logcat.flush()
        cmd = "echo \"%s\" >> \"%s\""
        subprocess.call(cmd % ((("D/autoTest: %s\n" % s),main._file_logcat)), shell=True)
    return True


def open_logcat_file(dir,prefix):
    st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H.%M')
    filename = dir+"/"+prefix+st+".logcat"
    print("opening file for log:%s" % filename)
    try:
        main._file_logcat = filename
        main._file_logcat_name = filename
    except IOError as err:
        print("unable to open file :%s %s" % (filename, err))
        main._file_logcat = None
    return main._file_logcat


def handler(signum, args):
    print "handling signal... %d" % signum
    if signum in [1, 2, 3, 15]:
        print 'Caught signal %s, exiting.' %(str(signum))
        if main.log_thread:
            main.log_thread.run_baby = False
            time.sleep(2)

        close_log_file()
        sys.exit()
    else:
        print 'Caught signal %s, ignoring.' %(str(signum))


def main():
    main.log_dir = "./logs"
    if not check_dir(main.log_dir):
        print ("unable to create %s" % main.log_dir)
    main._file_logcat = None
    main._file_logs = None
    main.log_thread = None
    # from AVCommon import logger
    # logger.init()
    args = parse_args()
    catchable = ['SIGINT','SIGQUIT','SIGHUP','SIGTERM']
    for i in catchable:
        signum = getattr(signal,i)
        signal.signal(signum,handler)

    command_dev = CommandsDevice(args.device)

    set_status(command_dev, "Test Start")

    exit(0)
    print """ prerequisiti specifici TEST :
                    skype presente
    """
    results = collections.OrderedDict()
    command_dev.sync_time()
    set_properties(command_dev, results)
    #commands_rcs = CommandsRCS(login_id=command_dev.uid, device_id=command_dev.device_id)
    if args.logcat:
        open_logcat_file(main.log_dir,results['device'].replace(' ', ''))
        main.log_thread = LogcatThread("`which adb` -s %s logcat -c && `which adb` -s %s logcat >> %s" % (command_dev.get_dev_serialno(), command_dev.get_dev_serialno(), main._file_logcat_name))
    if args.log:
        open_log_file(main.log_dir,results['device'].replace(' ', ''))
        printl("going to log in %s" % main._file_logs)

    try:
        if args.number:
            printl ("going to execute the test %d" %args.number)
            n = 1
            while n <= args.number:
                printl("run execution number %d" % n)
                res = test_device(command_dev, args, results)
                print str(results)
                if res:
                    break
                n += 1
        else:
            test_device(command_dev, args, results)
            print str(results)

    except Exception, ex:
        print ex
        traceback.print_exc()
        results['exception'] = ex
        print str(results)
    #print results
    #report = report_test_rail(results)
    #report_files(results, report)

    print "Fine."

    try:
        uid = command_dev.uid
    except:
        uid = 0

    say("test ended %s" % uid)
    print "Check manually with the evidences in the instance: %s" % (results.get('instance_name', "NO SYNC"))
    if args.logcat:
        main.log_thread.run_baby = False
        time.sleep(2)
    close_log_file()



if __name__ == "__main__":
    main()
