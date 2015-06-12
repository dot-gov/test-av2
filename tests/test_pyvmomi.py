import atexit
from operator import attrgetter
import os
import sys
import threading
import time
import shutil

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
# "pm_revert_last_snapshot", "pm_create_snapshot"
action = "pm_list_snapshots"

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


def execute(si, target_vm):
    tools_status = target_vm.guest.toolsStatus
    if (tools_status == 'toolsNotInstalled' or
            tools_status == 'toolsNotRunning'):
        raise SystemExit(
            "VMwareTools is either not running or not installed. "
            "Rerun the script after verifying that VMWareTools "
            "is running")

    creds = vim.vm.guest.NamePasswordAuthentication(username=guestusr, password=guestpwd)

    content = si.RetrieveContent()

    #spec = vim.vm.guest.ProcessManager.WindowsProgramSpec(programPath="cmd.exe", arguments=" /c dir > c:\\AVTest\log.txt") # arguments="tmp.zip",  workingDirectory="C:\\AVTest\\"
    for i in range(0, 10):
        try:
            spec = vim.vm.guest.ProcessManager.WindowsProgramSpec(programPath="cmda.exe", arguments=" /c timeout 7") # arguments="tmp.zip",  workingDirectory="C:\\AVTest\\"

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


def pm_revert_last_snapshot(target_vm):
    task = target_vm.RevertToCurrentSnapshot_Task()
    while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
        time.sleep(1)
    return task.info.state == vim.TaskInfo.State.success


def pm_create_snapshot(target_vm, name):
    task = target_vm.CreateSnapshot_Task(name, "Auto snapshot by Rite", False, False)
    while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
        time.sleep(1)
    return task.info.state == vim.TaskInfo.State.success


def pm_remove_snapshot(snapshot):
    #it's VERY VERY important to set the flag to false, or it will remove all the subtree!
    task = snapshot.RemoveSnapshot_Task(removeChildren=False)
    while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
        time.sleep(1)
    return task.info.state == vim.TaskInfo.State.success


def pm_clean_snapshots(target_vm):
    snap_list = pm_list_snapshots(target_vm)
    for i in snap_list:
        if False:
            ret = pm_remove_snapshot(i)


def pm_list_snapshots(target_vm):
    snapshot = target_vm.snapshot #  snapshot.while tree[0].childSnapshotList is not None:
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

    elif action == "execute":
        myvm = get_vm_from_name(vm_name, si)
        if not isinstance(myvm, vim.VirtualMachine):
            print "could not find a virtual machine with the name %s (it's not a VM Instance)" % vm_name
            sys.exit(-1)
        execute(si, target_vm=myvm)

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

    sys.exit(0)

if __name__ == "__main__":
    script()

