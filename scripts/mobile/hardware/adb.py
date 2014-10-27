#!/usr/bin/python

import sys
import subprocess
import json
import re
import shutil
import threading
import os
from time import sleep
import zipfile
import time
import datetime

from multiprocessing import Process

# useful adb command which can be implemented
# Unlock your Android screen
#adb shell input keyevent 82

#Lock your Android screen
#adb shell input keyevent 6
#adb shell input keyevent 26

#Open default browser
#adb shell input keyevent 23

#Keep your android phone volume up(+)
#adb shell input keyevent 24

#Keep your android phone volume down(-)
#adb shell input keyevent 25

#Go to your Android Home screen
#adb shell input keyevent 3

#Take Screenshot from adb
#adb shell screenshot /sdcard/test.png
#Another Screen capture command
#screencap [-hp] [-d display-id] [FILENAME]
# -h: this message
# -p: save the file as a png.
# -d: specify the display id to capture, default 0

#start clock app
#adb shell am start com.google.android.deskclock

#stop clock app
#adb shell am force-stop com.google.android.deskclock

#start wifi settings manager
#adb shell am start -a android.intent.action.MAIN -n com.android.settings/.wifi.WifiSettings


#adb shell am start -n com.android.settings/.wifi.WifiStatusTest


#wifi on
#adb shell svc wifi enable

#wifi off
#adb shell svc wifi disable

#Mobile Data on
#adb shell svc data enable

#Mobile Data off
#adb shell svc data disable

#adb_path = "/Users/olli/Documents/work/android/android-sdk-macosx/platform-tools/adb"
devices = []  # we found with usb devices actually connected
adb_paths = ["adb", "/Users/zeno/Developer/adt-bundle-mac/sdk/platform-tools/adb"]
for adb_path in adb_paths:
    try:
        proc = subprocess.call([adb_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc:
            break
    except:
        continue

temp_remote_path = "/data/local/tmp/in/"
busybox_filename = 'busybox-android'


def call(cmd, device=None):
    if device:
        #print "##DEBUG## calling %s for device %s" % (cmd,device)
        proc = subprocess.call([adb_path,
                                "-s", device] + cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        #print "##DEBUG## calling %s" % cmd
        proc = subprocess.call([adb_path] + cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return proc != 0


def execute_no_command_split(cmd, device):
    #print "##DEBUG## calling %s for device %s" % (cmd,device)

    proc = subprocess.Popen([adb_path,
                             "-s", device, "shell", cmd], stdout=subprocess.PIPE)
    comm = proc.communicate()
    # proc.wait()
    return str(comm[0])


def skype_call(device=None):
    cmd = "am start -a android.intent.action.VIEW -d skype:echo123?call"
    return execute(cmd, device)


def viber_call(device=None):
    cmd = "am start -a android.intent.action.VIEW -d viber:"
    return execute(cmd, device)


def open_url(url, device=None):
    cmd = "am start -a android.intent.action.VIEW -d " + url
    return execute(cmd, device)


def press_key_home(device=None):
    cmd = "input keyevent 3"
    return execute(cmd, device)


def press_key_enter(device=None):
    cmd = "input keyevent 66"
    return execute(cmd, device)


def press_key_dpad_up(device=None):
    cmd = "input keyevent 19"
    return execute(cmd, device)


def press_key_dpad_down(device=None):
    cmd = "input keyevent 20"
    return execute(cmd, device)


def press_key_dpad_center(device=None):
    cmd = "input keyevent 23"
    return execute(cmd, device)


def insert_text_and_enter(text, device=None):
    cmd = "input text %s" % text
    execute(cmd, device)
    press_key_enter(device)


def press_key_menu(device=None):
    cmd = "input keyevent 1"
    return execute(cmd, device)


def press_key_tab(device=None):
    cmd = "input keyevent 61"
    return execute(cmd, device)


def press_key_power(device=None):
    cmd = "input keyevent 26"
    return execute(cmd, device)

def is_screen_locked(device=None):
    cmd = "dumpsys power "
    cmd = execute(cmd, device)
    match = re.findall('mLocks\.gather=\S+', cmd)
    if len(match) > 0 and match[0].lower().find("on_") != -1:
        return True
    return False

def is_screen_off(device=None):
    cmd = "dumpsys power "
    cmd = execute(cmd, device)
    match = re.findall('mScreenOn+=\S+', cmd)
    if len(match) > 0:
        if match[0].lower().find("false") != -1:
            return True
        else:
            return False
    elif cmd.find("SCREEN_ON_BIT") == -1:
        return True

    return False


def wait_and_click(dev_target, x=750, y=130):
    # (x, y, w, h) = dev_target.getRestrictedScreen()
    # width = int(w)
    # height = int(h)
    # print 'h = %s, w = %s' % (height, width)
    time.sleep(2)
    os.system(adb_path + " shell input tap %d %d") % (x, y)
    #dev_target.touch(750, 1230)
    time.sleep(6)


def unlock(device=None):
    if is_screen_locked(device):
        return True
    cmd = "input keyevent 82"
    execute(cmd, device)
    sleep(1)
    if not is_screen_locked(device):
        cmd = "input swipe 0 200 500 200"
        execute(cmd, device)
        sleep(1)
    return not is_screen_locked(device)


def set_screen_on_and_unlocked(device=None):
    if is_screen_off(device):
        press_key_power(device)
    unlock(device)


def set_screen_onOff_and_unlocked(device=None):
    if not is_screen_off(device):
        print "screen was on powering off"
        press_key_power(device)
    sleep(2)
    if is_screen_off(device):
        print "screen was off"
        press_key_power(device)
    return unlock(device)


def execute(cmd, device=None):
    #print "##DEBUG## calling '%s' for device %s" % (cmd, device)

    if device:
        proc = subprocess.Popen([adb_path,
                                 "-s", device,
                                 "shell"] + cmd.split(),
                                stdout=subprocess.PIPE)

    else:
        proc = subprocess.Popen([adb_path,
                                 "shell"] + cmd.split(),
                                stdout=subprocess.PIPE)

    comm = proc.communicate()
    ret = proc.returncode

    return str(comm[0])


def ps(device=None):
    pp = execute("ps", device).strip()
    return pp


def check_remote_process_change_pid(name, timeout=1, device=None, pid=-1):
    if pid == -1:
        while timeout > 0:
            pid = check_remote_process(name, device=device)
            if pid != -1:
                break
            timeout -= 1
    newPid = check_remote_process(name, timeout=timeout, device=device)
    if newPid != -1 and newPid != pid:
        return True
    print "Timout checking process %s change " % name
    return False


def check_remote_process_died(name, timeout=1, device=None):
    while timeout > 0:
        processes = ps(device)
        if len(processes) > 0 and processes.find(name) == -1:
            return True
        sleep(1)
        timeout -= 1
    print "Timout checking process %s death " % name
    return False


def check_remote_process(name, timeout=1, device=None):
    while timeout > 0:
        processes = ps(device)
        if len(processes) > 0 and processes.find(name) != -1:
            for i in processes.splitlines():
                if i.find(name) != -1:
                    return int(i.split()[1])
        sleep(1)
        timeout -= 1
    print "Timout checking process %s " % name
    return -1


def check_remote_app_installed(name, timeout=1, device=None):
    while timeout > 0:
        packages = get_packages(device)
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
        cmd = execute(cmd, device)
        match = re.findall('mFocusedActivity+:.*', cmd)
        if len(match) > 0:
            if match[0].find(name) != -1:
                return True
        sleep(1)
        timeout -= 1
    print "Timout checking activity %s " % name
    return False


def reboot(device=None):
    call("reboot", device)


def get_deviceid(device=None):
    cmd = "dumpsys iphonesubinfo"

    comm = execute(cmd, device)
    lines = comm.strip()
    print "lines: ", lines
    devline = lines.split("\n")[2]
    id = devline.split("=")[1].strip()

    if id == 'null':
        cmd = "settings get secure android_id"
        comm = execute(cmd, device)
        id = comm.strip()

    return id.replace('*', '')


def get_packages(device=None):
    packages = execute("pm list packages", device)
    p_list = []
    for p in packages.split():
        if ":" in p:
            p_list.append(p.split(':')[1])
    return p_list


def get_package_version(app,device=None):
    packages = execute("dumpsys package", device)
    pkg_info = ""
    copy = False
    patter = "Package [%s]" % app
    for line in packages.splitlines():
        if line.strip().find(patter) != -1:
            copy = True
        elif line.strip().find("Package [") != -1:
            copy = False
        elif copy:
            pkg_info += line

    if len(pkg_info) > 10:
        r = re.compile('versionName=(.*?) ')
        version = r.search(pkg_info)
        if version:
            v = version.group(1)
            return v
    return ""


def get_prop(property, device):
    cmd = "getprop %s" % property
    return execute(cmd, device).strip()


def get_properties(device=None):
    manufacturer = get_prop("ro.product.manufacturer", device)
    model = get_prop("ro.product.model", device)
    selinux = get_prop("ro.build.selinux.enforce", device)
    release_v = get_prop("ro.build.version.release", device)
    build_date = get_prop("ro.build.date.utc", device)
    iso_date = datetime.datetime.fromtimestamp(1367392279).isoformat()
    #    print manufacturer, model, selinux, release_v
    return {"manufacturer": manufacturer, "model": model, "selinux": selinux, "release": release_v,
            "build_date": iso_date}


#    for line in output.split('\\n'):
#        if 'Device ID' in line:
#            eq = line.find("=")
#            dev_id = line[eq+2:-2]
#            print dev_id
#    return dev_id

def install(apk, device=None):
    """ Install melted application on phone
    @param package full path
    @return True/False
    """
    #if os.path.exists(apk) == False:
    #	return False
    if device:
        proc = subprocess.call([adb_path,
                                "-s", device,
                                "install", apk])
        #,
        #stdout=subprocess.PIPE)
    else:
        proc = subprocess.call([adb_path,
                                "install", apk])
    if proc != 0:
        return False
    return True


def executeService(apk, device=None):
    """ Execute melted apk on phone
    @param apk class name to run (eg. com.roxy.angrybirds)
    @return True/False
    shell am  startservice -n $CLASS_PACK/
    """
    app = apk + '/.ServiceMain'
    if device:
        proc = subprocess.call([adb_path,
                                "-s", device,
                                "shell", "am", "startservice",
                                "-n", app], stdout=subprocess.PIPE)
    else:
        proc = subprocess.call([adb_path,
                                "shell", "am", "startservice",
                                "-n", app], stdout=subprocess.PIPE)
    if proc != 0:
        return False
    return True


def executeMonkey(app, device=None):
    if device:
        proc = subprocess.call([adb_path,
                                "-s", device,
                                "shell", "monkey", "-p",
                                app, "-c", "android.intent.category.LAUNCHER", "1"], stdout=subprocess.PIPE)
    else:
        proc = subprocess.call([adb_path,
                                "shell", "monkey", "-p",
                                app, "-c", "android.intent.category.LAUNCHER", "1"], stdout=subprocess.PIPE)
    if proc != 0:
        return False
    return True


def executeGui(apk, device=None):
    """ Execute melted apk on phone
    @param apk class name to run (eg. com.roxy.angrybirds)
    @return True/False
    shell am  startservice -n $CLASS_PACK/
    """
    app = apk + '/.gui.ASG'
    if device:
        proc = subprocess.call([adb_path,
                                "-s", device,
                                "shell", "am", "start",
                                "-n", app], stdout=subprocess.PIPE)
    else:
        proc = subprocess.call([adb_path,
                                "shell", "am", "start",
                                "-n", app], stdout=subprocess.PIPE)
    if proc != 0:
        return False
    return True


def install_by_gapp(url, app, device=None):
    if check_remote_app_installed(app, 3, device) != 1:
        open_url(url, device=device)
        if check_remote_activity("com.android.vending/com.google.android.finsky.activities.MainActivity", timeout=60, device=device):
            for i in range(10):
                press_key_dpad_up(device=device)
            for i in range(2):
                press_key_dpad_down(device=device)
            press_key_dpad_center(device=device)
            for i in range(25):
                if check_remote_activity("com.android.vending/com.google.android.finsky.activities.AppsPermissionsActivity", timeout=5, device=device):
                    press_key_dpad_down(device=device)
                else:
                    break
            press_key_dpad_center(device=device)
            if isDownloading(device, 5):
                timeout = 1360
                while timeout>0:
                    if not  isDownloading(device,1):
                        break;
                    timeout-=1
                old_pid = check_remote_app_installed(app, 10, device)
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
    return execute(cmd, device)


def set_auto_rotate_enabled(state, device=None):
    s=0
    if state:
        s=1
    cmd = " content insert --uri content://settings/system --bind name:s:accelerometer_rotation --bind value:i:%d" % s
    return execute(cmd, device)


def run_app(app, device_serial=None):
    packages = get_packages(device_serial)
    if len(packages) > 0:
        calc = [p for p in packages if app in p][0]
        executeMonkey(calc, device_serial)
        return check_remote_process(calc, 5, device_serial) != -1
    return False


def uninstall_with_calc(device_serial=None):
    packages = get_packages(device_serial)
    if len(packages) > 0:
        calc = [p for p in packages if "calc" in p and not "localc" in p][0]
        executeMonkey(calc, device_serial)
        return check_remote_process(calc, 5, device_serial) != -1
    return False


def isDownloading(devece, timeout=2):
    """
    com.android.providers.downloads/.DownloadService
    ServiceRecord
    dumpsys activity services
    /data/data/com.android.providers.downloads/cache/
    adb shell  "dumpsys activity services" | grep com.android.providers.downloads/.DownloadService | grep ServiceRecord
    """
    while timeout:
        result = execute("dumpsys activity services", devices)
        if len(result) > 0:
            for p in result.split():
                if result.find("ServiceRecord")!=-1:
                    if result.find("DownloadService")!=-1:
                        if result.find("com.android.providers.downloads")!=-1:
                            return True
        timeout -= 1
        sleep(1)
    return False


def uninstall(app_name, device_serial=None):
    """ Execute melted apk on phone
    @param app_name class name to run (eg. com.roxy.angrybirds)
    @return True/False
    """
    #print "##DEBUG## calling uninstall for device %s" % device
    if device_serial:
        proc = subprocess.call([adb_path,
                                "-s", device_serial,
                                "uninstall", app_name], stdout=subprocess.PIPE)
    else:
        #print "adb uninstall %s" % apk
        proc = subprocess.call([adb_path,
                                "uninstall", app_name], stdout=subprocess.PIPE)

    if proc != 0:
        return False

    return True


def get_attached_devices():
    devices = []
    #devices = ""
    # Find All devices connected via USB
    proc = subprocess.Popen([adb_path, "devices"], stdout=subprocess.PIPE)
    output = str(proc.communicate())

    for line in output.split('\\n'):
        if '\\t' in line:
            dev = line.split('\\t')[0]
            if dev:
                props = get_properties(dev)
                #devices += "device: %s model: %s %s\n" % (dev,props["manufacturer"],props["model"])
                devices.append((dev, "device: %s model: %s %s release: %s" % (
                    dev, props["manufacturer"], props["model"], props["release"])))
                #devices.append(dev)

    return devices


#ML
#Copy a single file to an implicit tmp directory
#The destination dir will be /data/local/tmp/in/ (it will be created if nonexistent)
def copy_tmp_file(file_local_path, device=None):
    #print "##DEBUG##  Copying a single file to an implicit tmp directory on device %s" % device

    copy_file(file_local_path, temp_remote_path, False, device)


def get_app_apk(app, localDir, device):
    remote_apk = execute("pm path %s" % app, device)
    if (len(remote_apk) <= 0):
        print "no apk found for %s" % app
        return -1;
    remote_apk = remote_apk.split(":")[1].replace(":","").rstrip()
    version = get_package_version(app, device)

    print "apk found for %s:\n%s ver=%s" % (app,remote_apk, version)
    if len(version):
        localapk = os.path.basename(remote_apk)+"-"+version
    else:
        localapk = os.path.basename(remote_apk)
    print "check local file %s" % localDir + localapk
    present = os.path.exists(localDir + localapk)
    print "check local file %s is present %s" % (localDir + localapk, present)
    if present:
        print "apk already present for %s:\n%s" % (app,remote_apk)
        return True
    get_remote_file(os.path.basename(remote_apk),os.path.dirname(remote_apk), localDir, True, device)
    if os.path.exists(localDir + os.path.basename(remote_apk)):
        os.rename( localDir + os.path.basename(remote_apk), localDir + localapk)
    return os.path.exists(localDir + localapk)


def remove_app(app, device):
    remove = execute("pm uninstall %s" % app, device)
    if len(remove) <= 0:
        if remove.find("Success")!=-1:
            return True
    return False


#ML
#Copy a single file to an explicit directory with unprivileged or ROOT privileges
#The destination dir will be created if nonexistent
#it uses a temp directory ("/data/local/tmp/in/") to pull the file and then with root privileges moves the file.
#if the destination is directory "/data/local/tmp/in/", then it doesn't move the file
def copy_file(file_local_path, remote_path, root=False, device=None):
    #print "##DEBUG##  Copying a single file to a directory on device %s" % device

    #print "create dir %s" % remote_path
    #can always create temp dir without root
    executeSU("mkdir" + " " + temp_remote_path, False, device)

    #print "adb push %s" % file_local_path
    if device:
        proc = subprocess.call([adb_path,
                                "-s", device,
                                "push", file_local_path, temp_remote_path], stdout=subprocess.PIPE)
    else:
        proc = subprocess.call([adb_path,
                                "push", file_local_path, temp_remote_path], stdout=subprocess.PIPE)

    if remote_path != temp_remote_path:
        print "create remote destination %s" % remote_path
        print (executeSU("mkdir" + " " + remote_path, root, device))
        #print (executeSU("id", root, device))

        print "move the file to %s" % remote_path

        print (executeSU("dd" + " if=" + temp_remote_path + "/" + os.path.basename(
            file_local_path) + " of=" + remote_path + "/" + os.path.basename(file_local_path), root, device))


#Retrieves a single file from device temporary folder using adb pull
#local dir should exists!
#works only with temp dir (because does not use ROOT!)
def get_remote_temp_file(remote_filename, local_destination_path, device=None):
    print "%s" % local_destination_path
    assert os.path.exists(local_destination_path)

    remote_file_fullpath = temp_remote_path + "/" + remote_filename
    print "adb pull from=%s to=%s" % (remote_file_fullpath, local_destination_path)

    if device:
        proc = subprocess.call([adb_path,
                                "-s", device,
                                "pull", remote_file_fullpath, local_destination_path], stdout=subprocess.PIPE)
    else:
        proc = subprocess.call([adb_path,
                                "pull", remote_file_fullpath, local_destination_path], stdout=subprocess.PIPE)


#Retrieves a single file from device from any folder using dd and adb pull
#local dir should exists!
def get_remote_file(remote_source_filename, remote_source_path, local_destination_path, root=True, device=None):
    assert os.path.exists(local_destination_path)

    remote_file_fullpath_src = remote_source_path + "/" + remote_source_filename
    remote_file_fullpath_tmp = temp_remote_path + "/" + remote_source_filename

    print (executeSU("dd" + " if=" + remote_file_fullpath_src + " of=" + remote_file_fullpath_tmp, root, device))

    print (executeSU("chown " + "shell.shell" + " " + remote_file_fullpath_tmp, root, device))

    get_remote_temp_file(remote_source_filename, local_destination_path, device)

    remove_temp_file(remote_source_filename, device)


def check_remote_file(remote_source_filename, remote_source_path, timeout=1, device=None):
    remote_file_fullpath_src = remote_source_path + "/" + remote_source_filename

    while timeout:
        #print "checking %s" % "ls -l %s " % remote_file_fullpath_src
        res = executeSU("ls -l %s " % remote_file_fullpath_src, root=False, device=device)
        if len(res) > 0 and res.find("No such file or directory") == -1:
            return True
        sleep(1)
        #print "result: %s" % res
        timeout -= 1
    print "Timout checking %s " % "ls -l %s " % remote_file_fullpath_src
    return False


#ML
#deletes a single file
def remove_file(filename, file_path, root=False, device=None):
    print "##DEBUG##  Deleting a single file from device %s" % device

    toremove = file_path + "/" + filename

    print "removing file %s" % toremove

    executeSU("rm" + " " + toremove, root, device)


def remove_directory(dir_path, root=False, device=None):
    print "##DEBUG##  Deleting %s directory (rm -r) from device %s" % (dir_path, device)

    executeSU("rm -r" + " " + dir_path, root, device)


#ML
#deletes a single file from tmp
def remove_temp_file(filename, device=None):
    remove_file(filename, temp_remote_path, False, device)


def executeSU(cmd, root=False, device=None):
    if root:
        if device:
            proc = subprocess.Popen(
                [adb_path, "-s", device, "shell", "ddf qzx '" + cmd + "'"], stdout=subprocess.PIPE)
        else:
            proc = subprocess.Popen([adb_path, "shell", "ddf qzx '" + cmd + "'"], stdout=subprocess.PIPE)

        comm = proc.communicate()
        return str(comm[0])
    else:
        #print "##DEBUG## executing: %s withOUT dfi" % cmd
        return execute(cmd, device)


#This command installs busybox,
def install_busybox(local_path_with_filename, device=None):
    print 'Installing BusyBox'
    copy_tmp_file(local_path_with_filename)
    #renames file to default (busybox-android)
    #since it's just a rename I can use mv
    executeSU("mv" + " " + temp_remote_path + "/" + os.path.basename(
        local_path_with_filename) + " " + temp_remote_path + "/" + busybox_filename, False, device)


#NB: this command requires install_busybox!
def uninstall_busybox(device=None):
    print 'Removing BusyBox'
    remove_temp_file(busybox_filename, device)


#NB: this command requires install_busybox!
def execute_busybox(cmd, root=False, device=None):
    print 'Executing with BusyBox cmd= %s' % cmd
    executeSU(temp_remote_path + "/" + busybox_filename + " " + cmd, root, device)


def pack_remote(destination_path_and_filename, source_dir, root=False, device=None):
    print 'Packing'
    execute_busybox("tar -zcvf " + destination_path_and_filename + " " + source_dir, root, device)


def unpack_remote(source_path_and_filename, destination_dir, root=False, device=None):
    print 'Unpacking'
    execute_busybox("tar -zxvf " + source_path_and_filename + " -C " + destination_dir, root, device)


def pack_remote_to_local(remote_source_dir, local_path, local_filename, root=False, device=None):
    remote_file_fullpath = temp_remote_path + "/" + local_filename
    pack_remote(remote_file_fullpath, remote_source_dir, root, device)
    get_remote_temp_file(local_filename, local_path, device)
    remove_temp_file(local_filename, device)


def unpack_local_to_remote(local_file_path, local_filename, remote_dir, root=False, device=None):
    remote_file_fullpath = temp_remote_path + "/" + local_filename
    copy_tmp_file(local_file_path + "/" + local_filename, device)
    unpack_remote(remote_file_fullpath, remote_dir, root, device)
    remove_temp_file(local_filename, device)


# def backup_app_data(apk_conf_backup_file, package_name, device):
#     dev = device.serialno
#     #adb backup -f ./test.ab -noapk com.avast.android.mobilesecurity
#     # print os.path.abspath(apk_conf_backup_file)
#     # print package_name
#
#     def wait_and_click(dev_target):
#         (x, y, w, h) = dev_target.getRestrictedScreen()
#         width = int(w)
#         height = int(h)
#         print 'h = %s, w = %s' % (height, width)
#         sleep(2)
#         dev_target.touch(750, 1230)
#
#     p = Process(target=wait_and_click, args=(device,))
#     p.start()
#
#     if dev:
#         os.system(adb_path + " -s " + dev + " backup " + " -f " + apk_conf_backup_file + " -noapk " + package_name)
#
#     else:
#         os.system(adb_path + " backup " + " -f " + apk_conf_backup_file + " -noapk " + package_name)
#
#     p.join()


def backup_app_data(apk_conf_backup_file, package_name, device):
    __backup_restore_app_data(apk_conf_backup_file, device, True, package_name=package_name)


def restore_app_data(apk_conf_backup_file, device):
    __backup_restore_app_data(apk_conf_backup_file, device, False)


def __backup_restore_app_data(apk_conf_backup_file, device, backup, package_name=None):
    dev = device.serialno
    #adb backup -f ./test.ab -noapk com.avast.android.mobilesecurity
    # print os.path.abspath(apk_conf_backup_file)
    # print package_name


    p = Process(target=wait_and_click, args=(device,))
    p.start()

    # backup
    if backup:
        if dev:
            #-shared
            os.system(adb_path + " -s " + dev + " backup " + " -f " + apk_conf_backup_file + " -noapk " + package_name)
        else:
            os.system(adb_path + " backup " + " -f " + apk_conf_backup_file + " -noapk " + package_name)

    # restore
    else:
        if dev:
            os.system(adb_path + " -s " + dev + " restore " + apk_conf_backup_file)
        else:
            os.system(adb_path + " restore " + apk_conf_backup_file)

    p.join()


"""
	def run(self):
		#apk = 'kr.aboy.tools.zip'
		
		# Change configuration
		#print "Updating package %s with new configuration"  % self.apk
		#if not self.sync_conf():
		#	print "problem updating configuration fo %s." % self.apk
		#	sys.exit(1)
		
		# Unzip apk
		output_zip = os.path.join(conf.build_dir, self.apk)
		output_apk = self.unzip(output_zip)
		
		# Test with adb
		# 1. install
		print "Installing %s on %s" % (output_apk, self.device)
		installed = self.install(output_apk)
		if not installed:
			print "%s not installed on %s" % (output_apk,self.device)
			sys.exit(1)
		
		# 2. run on phone
		print "Executing %s on %s" % (output_apk, self.device)
		executed = self.execute(self.apk[:-4])
		if not executed:
			print "%s not executed on %d" % (output_apk,self.device)
			sys.exit(1)
		
		# 3. check (sleep/wait stuff)
		sleep(10)
		
		# 4. assertions
		print "Checking for instances on %s" % self.device

		# 5. Uninstall phase
		print "This is the end, Uninstalling on %s" % self.device
		uninstalled = self.uninstall(self.apk[:-4])
		if not uninstalled:
			print "Uninstall with your Handz..."
			sys.exit(1)

"""

if __name__ == "__main__":
    print get_deviceid()
