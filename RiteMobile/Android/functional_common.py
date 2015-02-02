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

from check_common import Check

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


# apk_template = "build/android/install.%s.apk"
apk_template = "assets/autotest.%s.apk"

def say(text):
    os.system("say " + text)

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

def uninstall_agent(commands_device, c, results):
    c.uninstall()

    say("agent uninstall, verify request")
    if 'No' != results.get('root','No'):
        print "uninstall:without DIALOG"
        for i in range(12):
            time.sleep(10)

            processes = commands_device.get_processes()
            uninstall = Check.service not in processes
            if uninstall:
                break
    else:
        print "uninstall:DIALOG !!!"
        unistall_dialog_wait_and_press(commands_device, 120)

    print "uninstall: wait 30sec"
    time.sleep(30)
    results['uninstall'] = uninstall

    if not uninstall:
        print "uninstall: ERROR"
        print "processes: %s" % processes
        commands_device.uninstall_agent()
    else:
        print "uninstall: OK"

def unistall_dialog_wait_and_press(command_dev,timeout=60):
    if not command_dev.check_remote_activity("UninstallerActivity", timeout):
        res = "process dvci still running\n"
        print res
    else:
        command_dev.press_key_enter()
        command_dev.press_key_tab()
        command_dev.press_key_enter()
        time.sleep(4)

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


def report_if_exists(results, param):
    report = ""
    for p in param:
        report += "\t%s: %s\n" % (p, results.get(p, ""))
    return report


def report_build(results):
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
    report += "Asserts\n"
    report += report_if_exists(results, ["asserts"])
    #print report
    return report


def report_files(results, report):
    with open('report/test-%s.%s.txt' % (results.get('id', 0), results.get('device', "device")), 'ab') as tfile:
        tfile.write(report)

    # with open('report/test-%s.%s.csv' % (results.get('id', 0), results.get('device', "device")), 'ab') as csvfile:
    #     # write header
    #     devicelist = csv.writer(csvfile, delimiter=";",
    #                             quotechar="|", quoting=csv.QUOTE_MINIMAL)
    #     devicelist.writerow(results.values())

    with open('report/hardware.logs.txt', 'a+') as logfile:
        logfile.write(str(results))
        logfile.write("\n")

    with open('report/hardware.logs.py', 'a+') as logfile:
        logfile.write("h.append(collections." + str(results) + ")")
        logfile.write("\n")


def test_device(test_specific, commands_rcs, command_dev, args, results, demo = True,  persist = True):
    if args.fastnet:
        command_dev.wifi('open', check_connection=False, install=True)
        exit(0)

    if args.reboot:
        print "REBOOT"
        command_dev.reboot()

    if args.build or not os.path.exists('assets/autotest.default.apk'):
        print "BUILD"

        config = test_specific.get_config()

        config = config.replace("$(HOSTNAME)", commands_rcs.endpoint)
        if not os.path.exists("build"):
            os.makedirs("build")
        f = open("build/config.upload.json", "w")
        f.write(config)
        f.close()

        # push new conf
        os.system('ruby assets/rcs-core.rb -u %s -p %s -d %s -f %s -c build/config.upload.json' % (
            commands_rcs.login, commands_rcs.password, commands_rcs.host, commands_rcs.factory))

        params = {u'binary': {u'admin': True, u'demo': False, u'persist': True},
                  u'melt': {u'appname': u'autotest'},
                  u'package': {u'type': u'installation'},
                  u'platform': u'android'}

        params[u'binary'][u'demo'] = demo
        params[u'binary'][u'persist'] = persist

        if persist:
            print "PERSIST"
            params[u'package'][u'type']

        jparam = json.dumps(params)
        json_params = "build/params.json"
        f = open(json_params, "w")
        f.write(jparam)
        f.close()

        os.system(
            'ruby assets/rcs-core.rb -u %s -p %s -d %s -f %s -b %s -o and.zip' % (
                commands_rcs.login, commands_rcs.password, commands_rcs.host, commands_rcs.factory, json_params))
        os.system('unzip -o  and.zip -d assets')
        os.remove('and.zip')
    if not os.path.exists('assets/autotest.default.apk'):
        print "ERROR, cannot build apk"
        exit(0)

    print "SYNC TIME"
    command_dev.sync_time()
    set_properties(command_dev, results)

    print "UNLOCK"
    if command_dev.isVersion(4, 0, -1) > 0:
        command_dev.unlock_screen()
    else:
        command_dev.unlock()

    try:
        with commands_rcs as c:
            commands_rcs.delete_old_instance()

            # install agent and check it's running
            # todo: to install the agent, it'e more secure to
            # unistall via "calc" and then use pm uninstall
            if test_specific.check_install(command_dev, results):
                print "INSTALL"
                install(command_dev, results)
            else:
                return "old installation present"

            print "EXECUTE"
            results["executed"] = command_dev.execute_agent()
            if results["executed"]:
                print "... executed"
            else:
                return "execution failed"

            command_dev.press_key_home()

            # sync e verifica
            print "SYNC"
            c.wait_for_sync()

            # rename instance
            results['instance_name'] = c.rename_instance(results['device'])

            # check for root
            print "ROOT"
            results["su"] = command_dev.info_root()

            result, root, info = c.check_root()
            results['root'] = root
            results['root_first'] = result
            results['have_root'] = result

            test_specific.check_evidences(command_dev, c, results, "_first")

            print "TEST SPECIFIC"
            test_specific.test_device(args, command_dev, c, results)

            # evidences
            print "EVIDENCES"
            test_specific.check_evidences(command_dev, c, results, "_last")

        if args.interactive:
            say("press enter to uninstall %s" % id)
            ret = raw_input("... PRESS ENTER TO UNINSTALL\n")

        # uninstall
        print "UNINSTALL"
        uninstall_agent(command_dev, c, results)

        # check uninstall after reboot
        test_specific.check_uninstall(command_dev, results)

    except Exception, ex:
        traceback.print_exc()
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
    parser.add_argument('-d', '--device', required=False,
                        help="choose serial number of the device to use")

    args = parser.parse_args()

    return args


def test_functional_common(test_specific, CommandsRCS):
    args = parse_args()
    if args.device:
        command_dev = CommandsDevice(args.device)
    else:
        command_dev = CommandsDevice()

    results = collections.OrderedDict()

    commands_rcs = CommandsRCS(login_id=command_dev.uid, device_id=command_dev.device_id)

    try:
        test_device(test_specific, commands_rcs, command_dev, args, results)
    except Exception, ex:
        print ex
        traceback.print_exc()
        results['exception'] = ex

    results["result"] = test_specific.final_assertions(results)

    report = report_build(results)
    report_files(results, report)

    print report
    print "Fine."

    try:
        uid = command_dev.uid
    except:
        uid = 0

    say("test ended %s" % uid)
    print "Check manually with the evidences in the instance: %s" % (results.get('instance_name', "NO SYNC"))

    return results

