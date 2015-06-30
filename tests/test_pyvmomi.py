import atexit
from datetime import datetime
from operator import attrgetter
import os
import sys
import threading
import time
import shutil
from requests.auth import HTTPBasicAuth

__author__ = 'mlosito'

from pyVim import connect
from pyVmomi import vim
import ssl
import requests

ssl._create_default_https_context = ssl._create_unverified_context

host = '172.20.20.126'
path = "/sdk"
user = 'avtest'
domain = 'vsphere.local'
pwd = 'Av!Auto456'
guestusr = 'avtest'
guestpwd = 'avtest'


#"list_vms" "poweron", "poweroff", "stress", "listfiles", "put_file", "get_file", "hard_poweroff", "get_vm_from_path", "pm_list_snapshots",
# "pm_revert_last_snapshot", "pm_create_snapshot", "pm_clean_snapshots", "pm_refresh_snapshots", "pm_revert_named_snapshot"
# "pm_make_directory", "print_powered_on_vms", "pm_screenshot", "pm_list_processes", "pm_delete_directory",  "pm_is_powered_on",  "pm_is_powered_off"
action = "pm_list_processes"

#dangerous! vm_others = ['AVAgent Win7 x64', 'AVAgent Win7 x86', 'AVAgent Win7 x86_v10_2if', 'AVAgent WinSrv2008 R2 x64', 'AVAgent-Win81-x64', 'ComodoTest', 'FunCH', 'FunFF', 'FunIE', 'HoneyDrive', 'Kali linux', 'Mac OS X', 'PuppetMaster_New', 'Puppet_Ubuntu', 'RCS-Achille', 'RCSTestSrv', 'RiteMaster-DEB-nu', 'Stratagem Honeypot', 'TEST-Win-2012', 'TestRail', 'UbuntuAgent', 'WinXP-RU', 'vCenterC', 'Win7-x86-CCleaner', 'Win7-TestAV', 'Win81-TestSpot', ]
#probably some of these are not in use
#removed: 'Win7-Ahnlab_New','Win7-Ahnlab_New2', 'Win7-SysCare','Win7-TrendM',
vm_rite = ['Win7-AVG', 'Win7-AVG15', 'Win7-Adaware_New', 'Win7-Avast', 'Win7-Avira', 'Win7-Avira15',
           'Win7-BitDef', 'Win7-CMCAV', 'Win7-ClamAV', 'Win7-Comodo', 'Win7-DrWeb', 'Win7-ESET', 'Win7-FSecure', 'Win7-Fprot', 'Win7-Gdata',
           'Win7-KIS14', 'Win7-MBytes_New', 'Win7-MSEssential', 'Win7-McAfee_New', 'Win7-Norton', 'Win7-Norton15', 'Win7-Panda', 'Win7-Spybot',
           'Win7-VBA32', 'Win7-Zoneal', 'Win8-AVG15', 'Win8-Avira15', 'Win8-BitDef15', 'Win8-Defender', 'Win8-KIS15',
           'Win8-Norman', 'Win8-Panda15', 'Win8-SysCare', 'Win8-TrendM15', 'Win8-ZoneAl', 'Win81-360ts', 'Win81-Comodo', 'Win81-ESET7',
           'Win81-Fortinet', 'Win81-Risint', 'WinXP-AVG32', 'WinXP-KIS']

vm_puppet = ['Puppet_Win7-Adaware_New', 'Puppet_Win7-Avast_New', 'Puppet_Win7-BitDef', 'Puppet_Win7-DrWeb', 'Puppet_Win7-ESET', 'Puppet_Win7-FSecure',
             'Puppet_Win7-KIS14_New', 'Puppet_Win7-KIS_New', 'Puppet_Win7-MBytes', 'Puppet_Win7-McAfee', 'Puppet_Win7-Norman', 'Puppet_Win7-Norton',
             'Puppet_Win7-Panda', 'Puppet_Win7-TrendM', 'Puppet_WinXP-Avast32', 'Puppet_WinXP-KIS', ]


#OTHER INTERESTING FUNCTIONS:
#vm.RebootGuest



def get_vm_from_name(vm_name, si):
    # search the root inventory (follows all folders of all objects)
    vm = None
    entity_stack = si.content.rootFolder.childEntity
    while entity_stack:
        entity = entity_stack.pop()
        # print entity.name
        if entity.name == vm_name:
            vm = entity
            del entity_stack[0:len(entity_stack)]
            print "Found VirtualMachine: %s Name: %s" % (vm, vm.name)
            return vm
        elif hasattr(entity, 'childEntity'):
            entity_stack.extend(entity.childEntity)
        elif isinstance(entity, vim.Datacenter):
            entity_stack.append(entity.vmFolder)
    return vm


def get_vm_from_path(si):
    # search the root inventory (follows all folders of all objects)
    vm = None
    index = si.content.searchIndex
    object_view = si.content.viewManager.CreateContainerView(si.content.rootFolder, [vim.Datacenter], False)

    vm = index.FindByDatastorePath(datacenter=object_view.view[0], path='[VMFuzz] Puppet_Win7-FSecure/Puppet_Win7-FSecure.vmx')
    print "Found VirtualMachine: %s Name: %s" % (vm, vm.name)
    return vm


#POWERON
def poweron_vm(target_vm):
    print "Powering on VM (vm = %s)" % target_vm.name
    if target_vm.runtime.powerState != vim.VirtualMachinePowerState.poweredOn:

        # now we get to work... calling the vSphere API generates a task...
        task = target_vm.PowerOn()

        while task.info.state not in [vim.TaskInfo.State.success,
                                      vim.TaskInfo.State.error]:
            time.sleep(1)
        if task.info.state == vim.TaskInfo.State.error:
            # some vSphere errors only come with their class and no other message
            print "Error powering on machine (vm = %s)" % target_vm.name
            print "error type: %s" % task.info.error.__class__.__name__
            print "found cause: %s" % task.info.error.faultCause
            for fault_msg in task.info.error.faultMessage:
                print fault_msg.key
                print fault_msg.message
            #not successful
            return False
    print "Powered on (vm = %s)" % target_vm.name
    #successful
    return True


#IF POWERON, FIRST POWEROFF
def shutdown_vm(target_vm):
    if target_vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
        # using time.sleep we just wait until the power off action
        # is complete. Nothing fancy here.
        print "The machine is Powered ON! Powering off...(vm = %s)" % target_vm.name
        # does not returns a task
        target_vm.ShutdownGuest()
        while target_vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
            time.sleep(1)
        print "Power is off.(vm = %s)" % target_vm.name


def hard_poweroff_vm(target_vm):
    if target_vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
        # using time.sleep we just wait until the power off action
        # is complete. Nothing fancy here.
        print "The machine is Powered ON! Powering off...(vm = %s)" % target_vm.name
        # does not returns a task
        target_vm.PowerOff()
        while target_vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
            time.sleep(1)
        print "Power is off.(vm = %s)" % target_vm.name

def pm_is_powered_on(target_vm):
    return target_vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn

def pm_is_powered_off(target_vm):
    return target_vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff

#CHECK WINDOWS STARTUP
def wait_vmtools_vm(target_vm):
    while vim.ManagedEntityStatus.green != target_vm.guestHeartbeatStatus:
        time.sleep(5)
        print "Waiting for vmtools (vm = %s - status = %s)" % (target_vm.name, target_vm.guestHeartbeatStatus)

    print "Windoze started! Hurray! (vm = %s - status = %s)" % (target_vm.name, target_vm.guestHeartbeatStatus)


def print_vm_info(target_vm):
    summary = target_vm.summary
    print("Name                 : ", summary.config.name)
    print("Path                 : ", summary.config.vmPathName)
    print("Guest                : ", summary.config.guestFullName)
    print('Instance UUID        : ', summary.config.instanceUuid)
    print('Bios UUID            : ', summary.config.uuid)
    print('Guest OS id          : ', summary.config.guestId)
    print('Host name            : ', target_vm.runtime.host.name)
    print('Last booted timestamp: ', target_vm.runtime.bootTime)

    annotation = summary.config.annotation
    if annotation is not None and annotation != "":
        print("Annotation : ", annotation)
    print("State      : ", summary.runtime.powerState)
    if summary.guest is not None:
        ip = summary.guest.ipAddress
        if ip is not None and ip != "":
            print("IP         : ", ip)
    if summary.runtime.question is not None:
        print("Question  : ", summary.runtime.question.text)
    print("")


#poweroff, then poweron and wait
def full_powerup_vm(vm_name, si):
    myvm = get_vm_from_name(vm_name, si)
    if not isinstance(myvm, vim.VirtualMachine):
        print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
        sys.exit(-1)
    print_vm_info(myvm)
    shutdown_vm(myvm)
    if action in ["poweron", 'stress']:
        if poweron_vm(myvm):
            wait_vmtools_vm(myvm)
        else:
            print "Error Powering Up (vm = %s)" % vm_name


#max number of files = maxResults, no pattern filter
def list_dir(si, target_vm, directory="C:\\nononogergs\\"):
    maxResults = 999
    tools_status = target_vm.guest.toolsStatus
    if (tools_status == 'toolsNotInstalled' or
            tools_status == 'toolsNotRunning'):
        raise SystemExit(
            "VMwareTools is either not running or not installed. "
            "Rerun the script after verifying that VMWareTools "
            "is running")

    creds = vim.vm.guest.NamePasswordAuthentication(username=guestusr, password=guestpwd)
    content = si.RetrieveContent()
    try:
        #returns GuestListFileInfo
        guest_list_file_info = content.guestOperationsManager.fileManager.ListFilesInGuest(target_vm, creds, directory, maxResults=maxResults)
        files = guest_list_file_info.files
        remaining = guest_list_file_info.remaining
        if remaining:
            print "Listing only the first %s files" % maxResults
        print "List directory output:"
        for f in files:
            print "%s" % f.path
    except IOError, e:
        print e
    #
    # files = vim.ListFilesInGuest(vm=target_vm, filePath=directory)
    # print files
    # return files


def put_file(si, target_vm, fil="/Users/mlosito/Downloads/sec_522_sfx.exe"):
    tools_status = target_vm.guest.toolsStatus
    if (tools_status == 'toolsNotInstalled' or
            tools_status == 'toolsNotRunning'):
        raise SystemExit(
            "VMwareTools is either not running or not installed. "
            "Rerun the script after verifying that VMWareTools "
            "is running")

    # filesize = os.path.getsize(fil)
    with open(fil, "r") as f:
        filecontent = f.read()

    filesize = len(filecontent)

    creds = vim.vm.guest.NamePasswordAuthentication(username=guestusr, password=guestpwd)
    content = si.RetrieveContent()
    fileatt = vim.vm.guest.FileManager.WindowsFileAttributes()
    url = content.guestOperationsManager.fileManager.InitiateFileTransferToGuest(target_vm, creds, "C:\\AVTest\\put.zip", fileatt, filesize, True)

    print url

    url = url.replace("*", host)

    r = requests.put(url, filecontent, verify=False)

    if r.status_code == 200:
        print "Ok, file put to guest!"
    else:
        print "Error %s" % r.status_code


def get_file(si, target_vm):
    tools_status = target_vm.guest.toolsStatus
    if (tools_status == 'toolsNotInstalled' or
            tools_status == 'toolsNotRunning'):
        raise SystemExit(
            "VMwareTools is either not running or not installed. "
            "Rerun the script after verifying that VMWareTools "
            "is running")

    creds = vim.vm.guest.NamePasswordAuthentication(username=guestusr, password=guestpwd)
    content = si.RetrieveContent()

    file_transfert_info = content.guestOperationsManager.fileManager.InitiateFileTransferFromGuest(target_vm, creds, "C:\\AVTest\\put.zip")

    print file_transfert_info.url

    url = file_transfert_info.url.replace("*", host)

    r = requests.get(url, stream=True, verify=False)

    if r.status_code == 200:
        with open("/tmp/get.tmp", 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
        print "Ok, got file from guest!"
    else:
        print "Error %s" % r.status_code


def pm_make_directory(si, target_vm, dir_name="C:\\gatto\\"):
    tools_status = target_vm.guest.toolsStatus
    if (tools_status == 'toolsNotInstalled' or
            tools_status == 'toolsNotRunning'):
        raise SystemExit(
            "VMwareTools is either not running or not installed. "
            "Rerun the script after verifying that VMWareTools "
            "is running")

    creds = vim.vm.guest.NamePasswordAuthentication(username=guestusr, password=guestpwd)
    content = si.RetrieveContent()
    try:
        print "Creating directory: %s" % dir_name
        content.guestOperationsManager.fileManager.MakeDirectoryInGuest(target_vm, creds, dir_name, createParentDirectories=True)
    except vim.fault.FileAlreadyExists:
        print "Directory %s already exists, skipping creation" % dir_name
        return True
    except:
        print "Error creating directory %s" % dir_name
        return False
    print "Directory %s created" % dir_name
    return True


def pm_delete_directory(si, target_vm, dir_name="C:\\gatto\\", recursive=True):
    tools_status = target_vm.guest.toolsStatus
    if (tools_status == 'toolsNotInstalled' or
            tools_status == 'toolsNotRunning'):
        raise SystemExit(
            "VMwareTools is either not running or not installed. "
            "Rerun the script after verifying that VMWareTools "
            "is running")

    creds = vim.vm.guest.NamePasswordAuthentication(username=guestusr, password=guestpwd)
    content = si.RetrieveContent()
    try:
        print "Removing directory: %s, with recursion = %s" % (dir_name, recursive)
        content.guestOperationsManager.fileManager.DeleteDirectoryInGuest(target_vm, creds, dir_name, recursive=recursive)
    except vim.fault.FileNotFound:
        print "Directory %s not found, skipping deletion" % dir_name
        return True
    except:
        print "Error deleting directory %s" % dir_name
        return False
    print "Directory %s deleted" % dir_name
    return True


#this is the ugliest of the pyvmomi funcions: it cleanly uses the api to create the screenshot
#but then the screenshot is saved ONTO VSPHERE (wtf?) and I retrieve it using the Web-Based Datastore Browser
#manually creating the url and using Basic hhtp authentication. That it's the SIMPLEST way!
#also this leaves the screenshot files onto vsphere, so I need to make another api call to delete it
# VMWare applies strictly the kiss logic
def pm_screenshot(si, target_vm, img_path):
    tools_status = target_vm.guest.toolsStatus
    if (tools_status == 'toolsNotInstalled' or
            tools_status == 'toolsNotRunning'):
        raise SystemExit(
            "VMwareTools is either not running or not installed. "
            "Rerun the script after verifying that VMWareTools "
            "is running")

    task = target_vm.CreateScreenshot_Task()

    while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
        time.sleep(1)
    if task.info.state == vim.TaskInfo.State.error:
        print "Impossible to create screenshot(vm = %s)" % target_vm.name

        return False
    #successful
    print task.info.result

    #result = [VMFuzz] Puppet_Win7-FSecure/Puppet_Win7-FSecure-2.png
    store, filen = task.info.result.split(" ")
    store = store[1:-1]
    # url = https://172.20.20.126/folder/Puppet_Win7-FSecure/Puppet_Win7-FSecure-1.png?dcPath=Rite&dsName=VMFuzz
    url = "https://" + host + "/folder/" + filen + "?dcPath=Rite&dsName=" + store
    print url

    r = requests.get(url, stream=True, verify=False, auth=HTTPBasicAuth(domain+"\\"+user, pwd))

    if r.status_code == 200:
        with open("/tmp/get.png", 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
        print "Ok, got file from guest!"
    else:
        print "Error %s" % r.status_code
        return False

    print "Screenshot saved (vm = %s)" % target_vm.name

    content = si.RetrieveContent()
    task_del = content.fileManager.DeleteDatastoreFile_Task(url)
    while task_del.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
        time.sleep(1)
    if task_del.info.state == vim.TaskInfo.State.error:
        print "Impossible to delete screenshot file from vSphere (vm = %s)" % target_vm.name
        return False

    print "Temporary screenshot file %s deleted from vSphere" % filen
    return True


def execute(si, target_vm):
    tools_status = target_vm.guest.toolsStatus
    if (tools_status == 'toolsNotInstalled' or
            tools_status == 'toolsNotRunning'):
        raise SystemExit(
            "VMwareTools is either not running or not installed. "
            "Rerun the script after verifying that VMWareTools "
            "is running")

    creds = vim.vm.guest.NamePasswordAuthentication(username=guestusr, password=guestpwd)
    creds.interactiveSession = True

    content = si.RetrieveContent()

    #spec = vim.vm.guest.ProcessManager.WindowsProgramSpec(programPath="cmd.exe", arguments=" /c dir > c:\\AVTest\log.txt") # arguments="tmp.zip",  workingDirectory="C:\\AVTest\\"
    for i in range(0, 10):
        try:
            spec = vim.vm.guest.ProcessManager.WindowsProgramSpec(programPath="calc.exe", workingDirectory="C:\\Windows\\", arguments="", startMinimized=False) # arguments="tmp.zip",  workingDirectory="C:\\AVTest\\"

            pid = content.guestOperationsManager.processManager.StartProgramInGuest(target_vm, creds, spec)
        except vim.fault.FileNotFound, e:
            print e
            print "File to execute not found"
            return False
        print pid
        while True:
            guest_process_info = content.guestOperationsManager.processManager.ListProcessesInGuest(target_vm, creds, [pid])
            if guest_process_info[0].endTime:
                print "Program finished"
                return True
            time.sleep(2)
            print "I love busy waiting"


def pm_list_processes(si, target_vm):

    tools_status = target_vm.guest.toolsStatus
    if (tools_status == 'toolsNotInstalled' or
            tools_status == 'toolsNotRunning'):
        raise SystemExit(
            "VMwareTools is either not running or not installed. "
            "Rerun the script after verifying that VMWareTools "
            "is running")

    creds = vim.vm.guest.NamePasswordAuthentication(username=guestusr, password=guestpwd)

    content = si.RetrieveContent()

    out = []

    #gets process info for all the pids (no "pids" parameter (list) is specified)
    guest_process_info = content.guestOperationsManager.processManager.ListProcessesInGuest(target_vm, creds)
    for gpi in guest_process_info:
        # print gpi
           # name = 'slui.exe',
           # pid = 3904L,
           # owner = 'WIN7FSECURE\\avtest',
           # cmdLine = 'slui.exe',
           # startTime = 2015-06-19T12:43:58Z,
           # endTime = <unset>,
           # exitCode = <unset>
        if not gpi.endTime:
            out.append((gpi.name, gpi.pid, gpi.owner, gpi.cmdLine, gpi.startTime))
    for o in out:
        print o
    return out

def pm_revert_last_snapshot(target_vm):
    task = target_vm.RevertToCurrentSnapshot_Task()
    while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
        time.sleep(1)
    return task.info.state == vim.TaskInfo.State.success


def pm_revert_named_snapshot(target_vm, snapshot_name):
    #list all snapshots
    snap_list = pm_list_snapshots(target_vm)
    snap_list.reverse()
    for i in snap_list:
        print i.name
        if i.name == snapshot_name:
            task = i.snapshot.RevertToSnapshot_Task()
            while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                time.sleep(1)
            print "Task revert to %s ended with success: %s " % (snapshot_name, task.info.state == vim.TaskInfo.State.success)
            return task.info.state == vim.TaskInfo.State.success

    print "no snapshot with name %s found" % snapshot_name
    return False


def pm_create_snapshot(target_vm, name=""):
    if name == "":
        date = datetime.now().strftime('%Y%m%d-%H%M')
        name = "auto_%s" % date

    task = target_vm.CreateSnapshot_Task(name, "Auto snapshot by Rite - pyvmomi", False, False)
    while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
        time.sleep(1)
    return task.info.state == vim.TaskInfo.State.success


def pm_remove_snapshot(snapshot):
    #it's VERY VERY important to set the flag to false, or it will remove all the subtree!
    print "Removing snapshot... "
    task = snapshot.RemoveSnapshot_Task(removeChildren=False)
    while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
        time.sleep(1)

    if task.info.state == vim.TaskInfo.State.success:
        print "Removed snapshot SUCCESS!"
        return True
    else:
        print "Removing snapshot FAILED!"
        return False


def pm_refresh_snapshots(target_vm):
    ret1 = pm_create_snapshot(target_vm)
    if ret1:
        return pm_clean_snapshots(target_vm)
    else:
        return False


def pm_clean_snapshots(target_vm):
    snap_list = pm_list_snapshots(target_vm)
    snap_list.reverse()
    #keeps only the latest that is the first in list
    latest_auto_already_kept = 0
    if len(snap_list) > 2:
        for i in snap_list:
            print i.name
            if "manual" in i.name:
                print "I'll keep snapshot %s" % i.name
                continue
            elif "auto_" in i.name and latest_auto_already_kept < 2:
                print "I'll keep snapshot %s" % i.name
                latest_auto_already_kept += 1
                continue
            else:
                print "I'll remove snapshot %s" % i.name
                ret = pm_remove_snapshot(i.snapshot)
                #it removes just one snapshot and exits
                if not ret:
                    return False
    else:
        print "Nothing to remove."
    return True


def pm_list_snapshots(target_vm):
    snapshot = target_vm.snapshot  # snapshot.while tree[0].childSnapshotList is not None:
    l = []
    tree = snapshot.rootSnapshotList
    l.extend(tree)

    for i in l:
        # print("Name: %s - Description: %s - Time: %s" % (i.name, i.description, i.createTime))
        if i.childSnapshotList:
            l.extend(i.childSnapshotList)
    # print "UNSorted:"
    # for y in l:
    #     print("Name: %s - Description: %s - Time: %s" % (y.name, y.description, y.createTime))
    s = sorted(l, key=attrgetter('createTime'))
    print "Printing list of snapshots from the tree, flattened and sorted"
    for y in s:
        print("Name: %s - Time: %s - Description: %s" % (y.name, y.createTime, y.description))
    return s
    # # for s in snap_list:
    # while tree[0].childSnapshotList:
    #     if len(tree[0].childSnapshotList) > 1:
    #         print "Multiple branches! I don't support that!"
    #     print("Name: %s - Description: %s - Time: %s" % (tree[0].name, tree[0].description, tree[0].createTime))
    #     tree = tree[0].childSnapshotList
    # print("Name: %s - Description: %s" % (tree[0].name, tree[0].description))


def print_all_vms(si):
    # search the root inventory (follows all folders of all objects)
    names = []
    entity_stack = si.content.rootFolder.childEntity
    while entity_stack:
        entity = entity_stack.pop()
        if isinstance(entity, vim.VirtualMachine):
            print entity.name
            names.append(entity.name)
        elif hasattr(entity, 'childEntity'):
            entity_stack.extend(entity.childEntity)
        elif isinstance(entity, vim.Datacenter):
            entity_stack.append(entity.vmFolder)
    names.sort()
    print names


# DISCLAIMER: it counts all the VSPHERE VM, also Rite, Puppet, TESTSPOT, vcenter, and all Puppet VMS
def print_powered_on_vms(si):
    # search the root inventory (follows all folders of all objects)
    vms = []
    entity_stack = si.content.rootFolder.childEntity
    while entity_stack:
        entity = entity_stack.pop()
        if isinstance(entity, vim.VirtualMachine):
            print "Found " + entity.name

            if entity.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                print "VM: " + entity.name + "powered ON on host: %s" % entity.runtime.host.QueryHostConnectionInfo().serverIp
                vms.append(entity)
            else:
                print "VM: " + entity.name + "powered OFF"
        elif hasattr(entity, 'childEntity'):
            entity_stack.extend(entity.childEntity)
        elif isinstance(entity, vim.Datacenter):
            entity_stack.append(entity.vmFolder)
    print "Number of powered on vms: %s" % len(vms)
    return vms


def stress_test(si):
    vm_thread_list = []
    for vm_name in vm_rite:
        vm_thread = threading.Thread(target=full_powerup_vm, args=(vm_name, si))
        vm_thread.start()
        print "Started thread for vm: %s" % vm_name
        vm_thread_list.append(vm_thread)
        time.sleep(10)
    print "ALL THREADS STARTED"
    alive = True
    while alive:
        #waits for threads
        alive = False
        for t in vm_thread_list:
            if t.isAlive():
                alive = True
            time.sleep(1)
    print "All threads ended"


def script():
    #'[VMFuzz] Puppet_Win7-MBytes/Puppet_Win7-MBytes.vmx'
    vm_name = 'Puppet_Win7-FSecure'  # this have branch in snapshots
    #vm_name = 'Puppet_Win7-MBytes'
    #vm_name = 'Puppet_Win7-Avast_New'
    #vm_name = 'Puppet_Win7-ESET'
    si = connect.SmartConnect(host=host, user=domain+"\\"+user, pwd=pwd)

    # doing this means you don't need to remember to disconnect your script/objects
    atexit.register(connect.Disconnect, si)

    if action == "list_vms":
        print_all_vms(si)

    elif action in["poweron", "poweroff"]:
        full_powerup_vm(vm_name, si)

    elif action == "stress":
        stress_test(si)

    elif action == "listfiles":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        list_dir(si, target_vm=myvm)

    elif action == "put_file":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        put_file(si, target_vm=myvm)

    elif action == "get_file":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        get_file(si, target_vm=myvm)

    elif action == "pm_make_directory":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        pm_make_directory(si, myvm)

    elif action == "pm_delete_directory":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        pm_delete_directory(si, myvm)

    elif action == "pm_screenshot":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        pm_screenshot(si, myvm, "")

    elif action == "execute":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        execute(si, target_vm=myvm)

    elif action == "pm_list_processes":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        pm_list_processes(si, target_vm=myvm)

    elif action == "hard_poweroff":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        hard_poweroff_vm(target_vm=myvm)

    elif action == "print_vm_info":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        print_vm_info(myvm)

    elif action == "pm_revert_last_snapshot":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        pm_revert_last_snapshot(myvm)

    elif action == "get_vm_from_name":
        get_vm_from_name(vm_name, si)

    elif action == "get_vm_from_path":
        get_vm_from_path(si)

    elif action == "pm_list_snapshots":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        pm_list_snapshots(myvm)

    elif action == "pm_create_snapshot":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        pm_create_snapshot(myvm, "auto_test_yeah")

    elif action == "pm_clean_snapshots":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        pm_clean_snapshots(myvm)

    elif action == "pm_refresh_snapshots":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        pm_refresh_snapshots(myvm)

    elif action == "pm_revert_named_snapshot":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        pm_revert_named_snapshot(myvm, "auto_20150609-1247")

    elif action == "pm_is_powered_on":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        if pm_is_powered_on(myvm):
            print("ON")

    elif action == "pm_is_powered_off":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        if pm_is_powered_off(myvm):
            print("OFF")

    elif action == "print_powered_on_vms":
        print_powered_on_vms(si)

    sys.exit(0)

if __name__ == "__main__":
    script()