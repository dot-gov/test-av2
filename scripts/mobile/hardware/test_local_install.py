from distutils.command.config import config
import sys
import csv
import traceback
import time
import os
import re

from adbclient import AdbClient
from time import sleep
# our files
import commands
from scripts.mobile.hardware.apk import apk_dataLoader
from scripts.mobile.hardware.utils import wifiutils, superuserutils, utils
import testmain
import adb



sys.path.append("/home/zad/work/devel/test-rite/")


def main(argv):
    devices = adb.get_attached_devices()


    if len(sys.argv) < 3:
        print "Usage:%s device init" %sys.argv[0]
        print "device= serial number or '.*'"
        print "init=y|n"
        exit(0)

    print "devices connessi:"
    for device in devices:
        print device

    if not devices:
        print "non ci sono device connessi"
        exit(0)
    else:
        if len(devices) > 1:
            dev = raw_input("su quale device si vuole eseguire il test? ")
            print "Eseguo il test su %s" % dev

    serialno = sys.argv[1]
    init = sys.argv[2]

    device = AdbClient(serialno=serialno)

    if init == "y":
        print "Init!"
        commands.init_device(device.serialno, install_eicar=False)

    dev = device.serialno
    res = ""
    retrive_app_list(dev,"/home/zad/list_links.txt")
  #  print "Test Execution success:%s" % test_local_install(device, res, wait_root=False)
  #  print "Test Execution success:%s" % test_local_install(device, res, persistent=False)
  #  print "Test Execution success:%s" % test_local_install(device, res)

def retrive_app_list(device, fname):
    if not superuserutils.install_ddf_shell(device):
        exit()
    with open(fname) as f:
        for line in f:
            if "https://play.google.com/store/apps/" in line:
                r = re.compile('\?id=(.*?)&rdid')
                m = r.search(line)
                if m:
                    app = m.group(1)
                    print "ready to get app=%s %s" % (app,line)
                    get_app(device, line, app)



def get_app(device, url, app_name):
    adb.press_key_home(device)
    adb.set_screen_onOff_and_unlocked(device)
    adb.kill_app("com.android.vending")
    sleep(3)
    if adb.install_by_gapp(url, app_name, device):
        print "app_name %s installed" % app_name
        if adb.get_app_apk(app_name, "./", device):
            print "apk %s retrived" % app_name
        else:
            print "failed to retrive apk %s" % app_name
        adb.uninstall(app_name,device)
        return
    print "app_name %s failed" % app_name


def test_local_install(device, results, reboot=False, persistent=True, wait_root=True):
    print "##################################################"
    print "#### STAGE 1 : TESTING Local Installation    #####"
    print "# reboot=%s persistent=%s wait Root=%s #" % (reboot, persistent, wait_root)
    print "##################################################"

    dev = device.serialno
    step = 1
    demo = True
    factory = 'RCS_0000001546'
    app_name = "autotest%s" % dev
    apk_out_name = 'assets/%s.default.apk' % app_name
    json_to = "build.%s.json" % app_name
    if demo:
        json = "build.demo.json"
    else:
        json = "build.nodemo.json"

    print "#STEP %d BUILD AGENT \"%s\" " % (step, apk_out_name)
#   commands.can_ping_google(dev)
    commands.modify_json_app_name(app_name, json_to, json)
    commands.build_apk_ruby(rebuild=False, user="zenobatch", password="castoreP123", server="castore",
                                conf_json_filename=json_to, factory_id=factory, apk_path_and_filename=apk_out_name)
    if not os.path.exists(apk_out_name):
        print "ERROR, cannot build apk"
        exit(0)

    step += 1

    adb.set_screen_on_and_unlocked(dev)
    print "#STEP %d GET ZYGOTE " % step
    zygote_pid = adb.check_remote_process("zygote", 30, dev)
    if zygote_pid == -1:
        res = "step %d: Fail to get zygote pid \n" % step
        print res
        results += res
        return False
    step += 1
    print "#STEP %d INSTALLING AGENT" % step
    agent = apk_dataLoader.get_apk('agent')
    adb.install(apk_out_name, dev)
    step += 1

    print "#STEP %d LAUNCHING AGENT" % step
    if agent.start_default_activity(dev).find("can't find") != -1:
        res = "step %d: fail to launch\n" % step
        print res
        results += res
        return False
    step += 1

    print "#STEP %d WAIT AGENT " % step
    old_pid = adb.check_remote_process("com.android.dvci", 30, dev)
    if old_pid == -1:
        res = "step %d: Fail to run the agent \n" % step
        print res
        results += res
        return False
    step += 1


    print "#STEP %d EXIT AGENT GUI" % step
    adb.press_key_home(dev)
    step += 1

    if wait_root:
        print "#STEP %d WAIT LOCAL ROOT" % step
        if not adb.check_remote_file("ddf", "/system/bin", timeout=180, device=dev):
            res = "step %d: Root not acquired\n" % step
            print res
            results += res
            return results
        step += 1

    if wait_root and persistent:
        print "#STEP %d CHECK Persistency" % step
        if not adb.check_remote_file("StkDevice.apk", "/system/app", timeout=20, device=dev):
            res = "step %d: check Persistence failed\n" % step
            print res
            results += res
            reboot = False
        step += 1

        print "#STEP %d CHECK change of pid %s" % (step, old_pid)
        if not adb.check_remote_process_change_pid("com.android.dvci", timeout=40, device=dev, pid=old_pid):
            res = "step %d: check pid change failed\n" % step
            print res
            results += res
            reboot = False
        step += 1


    if reboot:
        print "#STEP %d Reboot before unistall" % step
        adb.reboot(dev)
        if adb.check_remote_process("com.android.dvci", 30, dev) == -1:
            res = "step %d: reboot failed\n" % step
            print res
            results += res
            return results
    step += 1

    print "#STEP %d RUN UNISTALL" % step
    adb.uninstall_with_calc(dev)
    step += 1

    if not wait_root:
        print "#STEP %d WAIT UNISTALL DIALOG" % step
        if not adb.check_remote_activity("UninstallerActivity", timeout=60, device=dev):
            res = "step %d: process dvci still running\n" % step
            print res
            results += res
            return results
        else:
            adb.press_key_tab(dev)
            adb.press_key_tab(dev)
            adb.press_key_enter(dev)
            sleep(4)
        step += 1


    print "#STEP %d CHECK UNISTALL" % step
    if not adb.check_remote_process_died("com.android.dvci", timeout=60, device=dev):
        res = "step %d:UNISTALL fail, process dvci still running\n" % step
        print res
        results += res
        return results
    step += 1

    if wait_root and persistent:
        if not adb.check_remote_file("StkDevice.apk", "/system/app", timeout=5, device=dev):
            res = "step %d: check unistall Persistence failed\n" % step
            print res
            results += res
            return results
        step += 1

    new_zygote_pid = adb.check_remote_process("zygote", 30, dev)
    if zygote_pid != new_zygote_pid:
        res = "step %d: Test failed zygote rebooted!!! \n" % step
        print res
        results += res
        return False

    results += "success with reboot=%s persistent=%s wait Root=%s" % (reboot, persistent,wait_root)
    return results


if __name__ == "__main__":
    main(sys.argv)
