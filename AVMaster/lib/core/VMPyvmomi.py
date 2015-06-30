from operator import attrgetter
from datetime import datetime
import requests
import shutil
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.connection import ConnectionError
from AVCommon.logger import logging

from time import sleep
from ConfigParser import ConfigParser

from pyVim import connect
from pyVmomi import vim


class VMPyvmomi:
    def __init__(self, config_file, vm_name):
        self.config = ConfigParser()
        self.config.read(config_file)

        # pyvmomi_host = 172.20.20.126
        # pyvmomi_host_path = /sdk
        self.pyvmomi_host = self.config.get("vsphere", "pyvmomi_host")
        self.pyvmomi_host_path = self.config.get("vsphere", "pyvmomi_host_path")

        self.domain = self.config.get("vsphere", "domain")
        self.user = self.config.get("vsphere", "user")
        self.passwd = self.config.get("vsphere", "passwd")

        self.guestuser = self.config.get("vm_config", "user")
        self.guestpasswd = self.config.get("vm_config", "passwd")

        self.vm_path = self.config.get("vms", vm_name)

        #for logs
        self.vm_name = vm_name

    def __enter__(self):
        self.si = connect.SmartConnect(host=self.pyvmomi_host, user=self.domain+"\\"+self.user, pwd=self.passwd)

        self.content = self.si.RetrieveContent()
        self.vm_object = self._get_vm_from_path_index()
        self.creds = vim.vm.guest.NamePasswordAuthentication(username=self.guestuser, password=self.guestpasswd)
        #this sets the session id to 1
        self.creds.interactiveSession = True

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        connect.Disconnect(self.si)

    #uses the datacenter index to find a vm path
    #should be faster!
    #works only with first datacenter
    def _get_vm_from_path_index(self):
        # search the root inventory (follows all folders of all objects)
        index = self.content.searchIndex
        object_view = self.content.viewManager.CreateContainerView(self.si.content.rootFolder, [vim.Datacenter], False)

        vm = index.FindByDatastorePath(datacenter=object_view.view[0], path=self.vm_path)
        print "Found VirtualMachine: %s Name: %s" % (vm, vm.name)
        return vm

    #lists all the vms and see if the path matches
    def _get_vm_from_path(self):
        # search the root inventory (follows all folders of all objects)
        vm = None
        entity_stack = self.si.content.rootFolder.childEntity
        while entity_stack:
            entity = entity_stack.pop()
            # print entity.name
            if isinstance(entity, vim.VirtualMachine):
                if entity.summary.config.vmPathName == self.vm_path:
                    vm = entity
                    del entity_stack[0:len(entity_stack)]
                    print "Found VirtualMachine: %s Name: %s" % (vm, vm.name)
                    return vm
            elif hasattr(entity, 'childEntity'):
                entity_stack.extend(entity.childEntity)
            elif isinstance(entity, vim.Datacenter):
                entity_stack.append(entity.vmFolder)
        return vm

    #POWERON
    def _poweron_vm(self):
        print "Powering on VM (vm = %s)" % self.vm_object.name
        if self.vm_object.runtime.powerState != vim.VirtualMachinePowerState.poweredOn:

            # now we get to work... calling the vSphere API generates a task...
            task = self.vm_object.PowerOn()

            while task.info.state not in [vim.TaskInfo.State.success,
                                          vim.TaskInfo.State.error]:
                sleep(1)
            if task.info.state == vim.TaskInfo.State.error:
                # some vSphere errors only come with their class and no other message
                print "Error powering on machine (vm = %s)" % self.vm_object.name
                print "error type: %s" % task.info.error.__class__.__name__
                print "found cause: %s" % task.info.error.faultCause
                for fault_msg in task.info.error.faultMessage:
                    print fault_msg.key
                    print fault_msg.message
                #not successful
                return False
        print "Powered on (vm = %s)" % self.vm_object.name
        #successful
        return True

    #CHECK WINDOWS STARTUP
    #this could be improved with this command: Wait-Tools
    def _wait_vmtools_vm(self):
        #i sleep 60 seconds because windows boot takes at least 30 seconds...
        elapsed = 60
        sleep(60)
        while vim.ManagedEntityStatus.green != self.vm_object.guestHeartbeatStatus:
            sleep(15)
            elapsed += 15
            print "Waiting for vmtools (vm = %s - status = %s)" % (self.vm_object.name, self.vm_object.guestHeartbeatStatus)
            #960 sceonds = 16 minutes
            if elapsed > 960:
                print "Startup timed out (no vmtools)"
                return False
        print "Windoze started! Hurray! (vm = %s - status = %s)" % (self.vm_object.name, self.vm_object.guestHeartbeatStatus)
        return True

    def _check_running(self):
        tools_status = self.vm_object.guest.toolsStatus
        if tools_status == 'toolsNotInstalled' or tools_status == 'toolsNotRunning':
            return "VMwareTools is either not running or not installed. Rerun the script after verifying that VMWareTools is running"
        else:
            return None

    def pm_poweron(self):
        return self._poweron_vm()

    def pm_is_powered_on(self):
        return self.vm_object.runtime.powerState == vim.VirtualMachinePowerState.poweredOn

    def pm_is_powered_off(self):
        return self.vm_object.runtime.powerState == vim.VirtualMachinePowerState.poweredOff

    def pm_poweron_and_check(self):
        if self._poweron_vm():
            return self._wait_vmtools_vm()
        else:
            print "Error Powering Up (vm = %s)" % self.vm_object.vm_name
            return False

    def pm_check_login(self):
        return self._wait_vmtools_vm()

    def pm_poweroff(self):
        if self.vm_object.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
        # using time.sleep we just wait until the power off action
        # is complete. Nothing fancy here.
            print "The machine is Powered ON! Powering off...(vm = %s)" % self.vm_object.name
            # does not returns a task
            self.vm_object.ShutdownGuest()
            elapsed = 0
            while self.vm_object.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                sleep(5)
                elapsed += 5
                if elapsed > 360:
                    print "Shutdown timed out. Forcing poweroff"
                    task = self.vm_object.PowerOff()
                    while task.info.state not in [vim.TaskInfo.State.success,
                                          vim.TaskInfo.State.error]:
                        sleep(1)
                    return False
            print "Power is off.(vm = %s)" % self.vm_object.name
            return True
        print "Need to poweroff but machine is already off (vm = %s)" % self.vm_object.name
        return False

    #NB: it returns a LIST and not a string with multiple lines!
    #in case of error it returns a string
    def pm_list_directory(self, args):
        d = args[0]
        # logging.debug("Directory type %s" % type(d))
        max_results = 999
        filelist = []
        err = self._check_running()
        if err:
            return err
        try:
            #returns GuestListFileInfo
            guest_list_file_info = self.content.guestOperationsManager.fileManager.ListFilesInGuest(vm=self.vm_object, auth=self.creds, filePath=d, maxResults=max_results)
            files = guest_list_file_info.files
            remaining = guest_list_file_info.remaining
            if remaining:
                logging.debug("Listing only the first %s files" % max_results)
            logging.debug("List directory output:")
            for f in files:
                logging.debug("%s" % f.path)
                filelist.append(f.path)
        except vim.fault.GuestOperationsUnavailable:
            logging.debug("ERROR: Cannot talk to vmtools on vm: %s" % self.vm_name)
            return "ERROR: Cannot talk to vmtools on vm: %s" % self.vm_name
        except vim.fault.FileNotFound:
            logging.debug("ERROR: The directory %s does not exists on vm %s" % (d, self.vm_name))
            return []
        except IOError, e:
            return e
        return filelist

    def pm_make_directory(self, args):
        dir_name = args[0]

        err = self._check_running()
        if err:
            return err

        try:
            print "Creating directory: %s" % dir_name
            self.content.guestOperationsManager.fileManager.MakeDirectoryInGuest(self.vm_object, self.creds, dir_name, createParentDirectories=True)
        except vim.fault.FileAlreadyExists:
            logging.debug("Directory %s already exists, skipping creation" % dir_name)
            return True
        except:
            logging.debug("Error creating directory %s" % dir_name)
            return False
        logging.debug("Directory %s created" % dir_name)
        return True

    def pm_delete_directory(self, args):
        dir_name = args[0]
        dir_name = dir_name.replace('/', '\\')
        recursive = True

        err = self._check_running()
        if err:
            return err

        try:
            print "Removing directory: %s, with recursion = %s" % (dir_name, recursive)
            self.content.guestOperationsManager.fileManager.DeleteDirectoryInGuest(self.vm_object, self.creds, dir_name, recursive=recursive)
        except vim.fault.FileNotFound:
            logging.debug("Directory %s not found, skipping deletion" % dir_name)
            return True
        except:
            logging.debug("Error deleting directory %s" % dir_name)
            return False
        logging.debug("Directory %s deleted" % dir_name)
        return True

    def pm_put_file(self, args):
        filename = args[0]
        destination = args[1]

        err = self._check_running()
        if err:
            return False

        # filesize = os.path.getsize(fil)
        with open(filename, "r") as f:
            filecontent = f.read()

        filesize = len(filecontent)

        fileatt = vim.vm.guest.FileManager.WindowsFileAttributes()
        url = self.content.guestOperationsManager.fileManager.InitiateFileTransferToGuest(self.vm_object, self.creds, destination,
                                                                                          fileatt, filesize, True)

        logging.debug(url)

        #in some cases the api may put a * instead of the hostname (by specification)
        url = url.replace("*", self.pyvmomi_host)

        try:
            r = requests.put(url, filecontent, verify=False)
        except ConnectionError as e:
            logging.debug("Error uploading file, ConnectionError exception: %s", str(e))
            return False

        if r.status_code == 200:
            logging.debug("Ok, file put to guest!")
            return True
        else:
            logging.debug("Error %s" % r.status_code)
            return False

    def pm_get_file(self, args):

        src_filename = args[0]
        destination = args[1]

        err = self._check_running()
        if err:
            return False
        try:
            file_transfert_info = self.content.guestOperationsManager.fileManager.InitiateFileTransferFromGuest(self.vm_object, self.creds, src_filename)
        except vim.fault.GuestOperationsUnavailable:
            logging.debug("Cannot get file: %s from VM: %s (GuestOperationsUnavailable)" % (src_filename, self.vm_name))
            return False
        except vim.fault.FileNotFound:
            logging.debug("Cannot get file: %s from VM: %s (FileNotFound)" % (src_filename, self.vm_name))
            return False
        logging.debug(file_transfert_info.url)

        #in some cases the api puts a * instead of the hostname (by specification)
        url = file_transfert_info.url.replace("*", self.pyvmomi_host)

        r = requests.get(url, stream=True, verify=False)

        if r.status_code == 200:
            with open(destination, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
            logging.debug("Ok, got file from guest!")
            return True
        else:
            logging.debug("Error %s" % r.status_code)
            return False

    # this works a little differently from executeCmd:
    # the command is executed in background and NO GUI IS SHOWN (even if you launch ie notepad.exe)
    # arguments (args[2]) is a string (not a list)
    # this starts the command and WAITS UNTIL THE PID exists no more (or timeout occurs after TIMEOUT minutes)
    # arguments are cmd and cmd_args, and you can specify a TIMEOUT ( default = 10 minutes) as third argument
    def pm_run_and_wait(self, args):
        timeout = 600  # 10 minutes
        pid = self.pm_run(args[0:2])
        if len(args) > 2:
            timeout = args[2]

        if not pid:
            return False
        else:
            elapsed = 0
            while elapsed < timeout:
                try:
                    guest_process_info = self.content.guestOperationsManager.processManager.ListProcessesInGuest(self.vm_object, self.creds, [pid])
                    if guest_process_info[0].endTime:
                        logging.debug("Execution on guest completed (pid = %s)" % pid)
                        return True
                #in case of exception it just passes.
                except vim.fault.GuestOperationsUnavailable:
                    pass
                sleep(2)
                elapsed += 2
                logging.debug("Waiting command execution on guest (pid = %s)" % pid)
        logging.debug("Execution on guest TIMEOUT after %s seconds (pid = %s)" % (elapsed, pid))
        return False

    # this works a little differently from executeCmd:
    # the command is executed in background and NO GUI IS SHOWN (even if you launch ie notepad.exe)
    # arguments (args[2]) is a string (not a list)
    # this starts the command and exits
    #
    # arguments are cmd and cmd_args
    def pm_run(self, args):
        cmd = args[0]
        if len(args) > 1:
            cmd_args = args[1]
        else:
            cmd_args = ""

        err = self._check_running()
        if err:
            return False

        #spec = vim.vm.guest.ProcessManager.WindowsProgramSpec(programPath="cmd.exe", arguments=" /c dir > c:\\AVTest\log.txt") # arguments="tmp.zip",  workingDirectory="C:\\AVTest\\"

        # non so perce' c'e' scritto questo for!
        # for i in range(0, 10):
        try:
            spec = vim.vm.guest.ProcessManager.WindowsProgramSpec(programPath=cmd, arguments=cmd_args)  # arguments="tmp.zip",  workingDirectory="C:\\AVTest\\"

            pid = self.content.guestOperationsManager.processManager.StartProgramInGuest(self.vm_object, self.creds, spec)
            logging.debug("Launched command %s with pid %s" % (cmd, pid))
            return pid
        except vim.fault.FileNotFound:
            logging.debug("Error executing command %s - the executable file was not found" % cmd)
            return False
        except Exception:
            logging.debug("Error executing command %s - unknown reason" % cmd)
            return False

    def pm_list_processes(self):
        logging.debug("Listing processes for vm %s" % self.vm_name)

        err = self._check_running()
        if err:
            return False

        out = []

        #gets process info for all the pids (no "pids" parameter (list) is specified)
        guest_process_info = self.content.guestOperationsManager.processManager.ListProcessesInGuest(self.vm_object, self.creds)
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
                out.append({"name": gpi.name, "pid": gpi.pid, "owner": gpi.owner, "cmd_line": gpi.cmdLine, "startTime": gpi.startTime})
        # for o in out:
        #     print o

        return out

    def pm_ip_addresses(self):
        err = self._check_running()
        if err:
            return False
        if self.vm_object.summary.guest is not None:
            ips = self.vm_object.summary.guest.ipAddress
            if ips is None or len(ips) == 0:
                return None

            logging.debug("IP: %s" % ips)
            if isinstance(ips, basestring):
                return [ips]
            elif isinstance(ips, list):
                return ips
            else:
                return None

    def _pm_list_snapshots(self):
        snapshot = self.vm_object.snapshot  # snapshot.while tree[0].childSnapshotList is not None:
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

    def pm_revert_last_snapshot(self):
        task = self.vm_object.RevertToCurrentSnapshot_Task()
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            sleep(1)
        if task.info.state == vim.TaskInfo.State.success:
            logging.debug("VM: %s reverted to current snapshot" % self.vm_name)
            return True
        else:
            logging.debug("Error reverting VM: %s" % self.vm_name)
            return False

    def pm_revert_named_snapshot(self, args):
        snapshot_name = args[0]
        #list all snapshots
        snap_list = self._pm_list_snapshots()
        snap_list.reverse()
        for i in snap_list:
            print i.name
            if i.name == snapshot_name:
                task = i.snapshot.RevertToSnapshot_Task()
                while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                    sleep(1)
                print "Task revert to %s ended with success: %s " % (snapshot_name, task.info.state == vim.TaskInfo.State.success)
                return task.info.state == vim.TaskInfo.State.success

        print "no snapshot with name %s found" % snapshot_name
        return False

    def pm_create_snapshot(self, args=None):
        if not args:
            name = ""
        else:
            name = args[0]
        if name == "":
            date = datetime.now().strftime('%Y%m%d-%H%M')
            name = "auto_%s" % date

        task = self.vm_object.CreateSnapshot_Task(name, "Auto snapshot by Rite - pyvmomi", False, False)
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            sleep(1)
        return task.info.state == vim.TaskInfo.State.success

    def _pm_remove_snapshot(self, snapshot):
        #it's VERY VERY important to set the flag to false, or it will remove all the subtree!
        print "Removing snapshot... "
        task = snapshot.RemoveSnapshot_Task(removeChildren=False)
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            sleep(1)
        if task.info.state == vim.TaskInfo.State.success:
            print "Removed snapshot SUCCESS!"
            return True
        else:
            print "Removing snapshot FAILED!"
            return False

    def pm_refresh_snapshots(self):
        ret1 = self.pm_create_snapshot()
        if ret1:
            return self._pm_clean_snapshots()
        else:
            return False

    def _pm_clean_snapshots(self):
        snap_list = self._pm_list_snapshots()
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
                    ret = self._pm_remove_snapshot(i.snapshot)
                    #it removes just one snapshot and exits
                    if not ret:
                        return False
        else:
            print "Nothing to remove."
        return True

    #this is the ugliest of the pyvmomi funcions: it cleanly uses the api to create the screenshot
    #but then the screenshot is saved ONTO VSPHERE (wtf?) and I retrieve it using the Web-Based Datastore Browser
    #manually creating the url and using Basic hhtp authentication. That it's the SIMPLEST way!
    #also this leaves the screenshot files onto vsphere, so I need to make another api call to delete it
    # VMWare applies strictly the kiss logic
    def pm_screenshot(self, args):
        img_path = args[0]
        err = self._check_running()
        if err:
            return False

        task = self.vm_object.CreateScreenshot_Task()

        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            sleep(1)
        if task.info.state == vim.TaskInfo.State.error:
            logging.debug("Impossible to create screenshot(vm = %s)" % self.vm_object.name)

            return False
        #successful, prints screenshot filename and path
        # logging.debug(task.info.result)
        #result is something like: [VMFuzz] Puppet_Win7-FSecure/Puppet_Win7-FSecure-2.png
        store, filen = task.info.result.split(" ")
        store = store[1:-1]
        # url = https://172.20.20.126/folder/Puppet_Win7-FSecure/Puppet_Win7-FSecure-1.png?dcPath=Rite&dsName=VMFuzz
        url = "https://" + self.pyvmomi_host + "/folder/" + filen + "?dcPath=Rite&dsName=" + store
        logging.debug("Downloading screenshot from: %s" % url)

        r = requests.get(url, stream=True, verify=False, auth=HTTPBasicAuth(self.domain+"\\"+self.user, self.passwd))

        if r.status_code == 200:
            with open(img_path, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
            logging.debug("Ok, got file from guest!")
        else:
            logging.debug("Error %s" % r.status_code)
            return False

        logging.debug("Screenshot saved (vm = %s)" % self.vm_object.name)

        task_del = self.content.fileManager.DeleteDatastoreFile_Task(url)
        while task_del.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            sleep(1)
        if task_del.info.state == vim.TaskInfo.State.error:
            logging.debug("Impossible to delete screenshot file from vSphere (vm = %s)" % self.vm_object.name)
            return False

        logging.debug("Temporary screenshot file %s deleted from vSphere" % filen)
        return True


    # replaces VMRun's refreshSnapshot
    # def pm_refresh_snapshot(self, vmx):
    #     untouchables = [ "_datarecovery_"] #"ready", "activated",
    #
    #     if config.verbose:
    #         logging.debug("[%s] Refreshing snapshot.\n" % vmx)
    #
    #     # create new snapshot
    #     date = datetime.now().strftime('%Y%m%d-%H%M')
    #     snapshot = "auto_%s" % date
    #     untouchables.append(snapshot)
    #
    #     self.createSnapshot(vmx, snapshot)
    #
    #     snaps = self.listSnapshots(vmx)
    #     logging.debug("%s: snapshots %s" % (vmx,snaps))
    #     if len(snaps) > 2:
    #         for s in snaps[0:-2]:
    #             logging.debug("checking %s" % s)
    #             if s not in untouchables: # and "manual" not in s:
    #                 logging.debug("deleting %s" % s)
    #                 self.deleteSnapshot(vmx, s)
    #             else:
    #                 logging.debug("ignoring %s" % s)