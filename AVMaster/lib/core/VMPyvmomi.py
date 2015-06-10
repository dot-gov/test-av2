import subprocess
import os
import ntpath
import requests
import shutil
from AVCommon.logger import logging

from time import sleep
from datetime import datetime
from ConfigParser import ConfigParser
from AVCommon import config

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

    def __enter__(self):
        self.si = connect.SmartConnect(host=self.pyvmomi_host, user=self.domain+"\\"+self.user, pwd=self.passwd)

        self.content = self.si.RetrieveContent()
        self.vm_object = self._get_vm_from_path_index()
        self.creds = vim.vm.guest.NamePasswordAuthentication(username=self.guestuser, password=self.guestpasswd)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        connect.Disconnect(self.si)

    #should be faster!
    #works only with first datacenter
    def _get_vm_from_path_index(self):
        # search the root inventory (follows all folders of all objects)
        index = self.content.searchIndex
        object_view = self.content.viewManager.CreateContainerView(self.si.content.rootFolder, [vim.Datacenter], False)

        vm = index.FindByDatastorePath(datacenter=object_view.view[0], path=self.vm_path)
        print "Found VirtualMachine: %s Name: %s" % (vm, vm.name)
        return vm

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
        elapsed = 0
        while vim.ManagedEntityStatus.green != self.vm_object.guestHeartbeatStatus:
            sleep(5)
            elapsed += 5
            print "Waiting for vmtools (vm = %s - status = %s)" % (self.vm_object.name, self.vm_object.guestHeartbeatStatus)
            if elapsed > 360:
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

    def pm_poweron_and_check(self):
        if self._poweron_vm():
            return self._wait_vmtools_vm()
        else:
            print "Error Powering Up (vm = %s)" % self.vm_object.vm_name
            return False

    #may become
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
        except IOError, e:
            return e
        return filelist

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

        r = requests.put(url, filecontent, verify=False)

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

        file_transfert_info = self.content.guestOperationsManager.fileManager.InitiateFileTransferFromGuest(self.vm_object, self.creds, src_filename)

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
    # this starts the command and WAITS UNTIL THE PID exists no more (or timeout occurs after 10 minutes)
    #
    # arguments are cmd and cmd_args, and you can specify a timeout as third argument
    def pm_run_and_wait(self, args):
        timeout = 600  # 10 minutes
        pid = self.pm_run(args[0:2])
        if len(args) > 2:
            timeout = args[2]
        if pid < 0:
            return False
        else:
            elapsed = 0
            while elapsed < timeout:
                guest_process_info = self.content.guestOperationsManager.processManager.ListProcessesInGuest(self.vm_object, self.creds, [pid])
                if guest_process_info[0].endTime:
                    logging.debug("Execution on guest completed (pid = %s)" % pid)
                    return True
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
        except:
            logging.debug("Error executing command %s" % cmd)
            return -1

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

    # def createSnapshot(self, vmx, snapshot):
    #     if config.verbose:
    #         logging.debug("[%s] Creating snapshot %s.\n" % (vmx, snapshot))
    #     self._run_cmd(vmx, "snapshot", [snapshot])
    #
    # def deleteSnapshot(self, vmx, snapshot):
    #     if config.verbose:
    #         logging.debug("[%s] Deleting snapshot %s.\n" % (vmx, snapshot))
    #     self._run_cmd(vmx, "deleteSnapshot", [snapshot])
    #
    # def revertSnapshot(self, vmx, snapshot):
    #     if config.verbose:
    #         logging.debug("[%s] Reverting snapshot %s.\n" % (vmx, snapshot))
    #     self._run_cmd(vmx, "revertToSnapshot", [snapshot])
    #
    # def refreshSnapshot(self, vmx, delete=True):
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
    #     if delete is True:
    #         snaps = self.listSnapshots(vmx)
    #         logging.debug("%s: snapshots %s" % (vmx,snaps))
    #         if len(snaps) > 2:
    #             for s in snaps[0:-2]:
    #                 logging.debug("checking %s" % s)
    #                 if s not in untouchables: # and "manual" not in s:
    #                     logging.debug("deleting %s" % s)
    #                     self.deleteSnapshot(vmx, s)
    #                 else:
    #                     logging.debug("ignoring %s" % s)
    #
    # def revertLastSnapshot(self, vmx):
    #     snap = self.listSnapshots(vmx)
    #     if len(snap) > 0:
    #
    #         for s in range(len(snap) - 1, -1, -1):
    #             snapshot = snap[s]
    #             if snapshot != "_datarecovery_":
    #                 self.revertSnapshot(vmx, snap[s])
    #                 return "[%s] Reverted with snapshot %s" % (vmx, snap[s])
    #             else:
    #                 logging.debug("snapshot _datarecovery_ found!")
    #         return "%s, ERROR: no more snapshot to try" % vmx
    #     else:
    #         return "%s, ERROR: no snapshots!" % vmx
    #
    # def mkdirInGuest(self, vmx, dir_path):
    #     if config.verbose:
    #         logging.debug("[%s] Creating directory %s.\n" % (vmx, dir_path))
    #     self._run_cmd(vmx, "CreateDirectoryInGuest", [
    #         dir_path], [vmx.user, vmx.passwd])
    #
    # def listDirectoryInGuest(self, vmx, dir_path):
    #     if config.verbose:
    #         logging.debug("[%s] Listing directory %s.\n" % (vmx, dir_path))
    #     return self._run_cmd(vmx, "listDirectoryInGuest", [dir_path], [vmx.user, vmx.passwd], popen=True)
    #
    # def deleteDirectoryInGuest(self, vmx, dir_path):
    #     if config.verbose:
    #         logging.debug("[%s] Delete directory %s.\n" % (vmx, dir_path))
    #     self._run_cmd(
    #         vmx, "deleteDirectoryInGuest", [dir_path], [vmx.user, vmx.passwd])
    #
    # def copyFileToGuest(self, vmx, src_file, dst_file):
    #     if config.verbose:
    #         logging.debug("[%s] Copying file from %s to %s.\n" %
    #                      (vmx, src_file, dst_file))
    #     return self._run_cmd(vmx, "CopyFileFromHostToGuest",
    #                          [src_file, dst_file], [vmx.user, vmx.passwd])
    #
    # def copyFileFromGuest(self, vmx, src_file, dst_file):
    #     if config.verbose:
    #         logging.debug("[%s] Copying file from %s to %s.\n" %
    #                      (vmx, src_file, dst_file))
    #     return self._run_cmd(vmx, "CopyFileFromGuestToHost",
    #                          [src_file, dst_file], [vmx.user, vmx.passwd])
    #
    # def executeCmd(self, vmx, cmd, args=[], timeout=40, interactive=True, bg=False):
    #     if config.verbose:
    #         logging.debug("[%s] Executing %s with args %s" % (vmx, cmd, str(args)))
    #     if config.verbose:
    #         logging.debug("on %s with credentials %s %s" % (vmx, vmx.user, vmx.passwd))
    #         logging.debug("Options: timeout: %s, interactive: %s, background: %s" % (timeout, interactive, bg))
    #     cmds = []
    #     if interactive is True:
    #         cmds.append("-interactive")
    #     cmds.append(cmd)
    #     cmds.extend(args)
    #     if config.verbose:
    #         logging.debug("background execution is %s" % bg)
    #     return self._run_cmd(vmx,
    #                          "runProgramInGuest",
    #                          cmds,
    #                          [vmx.user, vmx.passwd],
    #                          bg=bg, timeout=timeout)
    #

    # def listProcesses(self, vmx):
    #     if config.verbose:
    #         logging.debug("[%s] List processes\n" % vmx)
    #     return self._run_cmd(vmx, "listProcessesInGuest", vmx_creds=[vmx.user, vmx.passwd], popen=True)
    #
    # def takeScreenshot(self, vmx, out_img):
    #     if config.verbose:
    #         logging.debug("[%s] Taking screenshot.\n" % vmx)
    #     if config.verbose:
    #         logging.debug("CALLING FUNCTIONS WITH out img %s, u: %s, p: %s.\n" % (out_img, vmx.user, vmx.passwd))
    #     self._run_cmd(vmx, "captureScreen", [out_img], [vmx.user, vmx.passwd])
    #     return os.path.exists(out_img)
    #
    # def VMisRunning(self, vmx):
    #     res = self._run_cmd(vmx, "list", popen=True)
    #     if vmx.path[1:-1] in res:
    #         return True
    #     return False
    #
    # def listSnapshots(self, vmx):
    #     out = self._run_cmd(vmx, "listSnapshots", popen=True).split("\n")
    #     return out[1:-1]
