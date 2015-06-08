import os
import sys
from AVCommon.logger import logging
from time import sleep
from AVCommon import mq
from AVCommon import helper
from AVCommon import config

def get_status(vm):
    from AVMaster import vm_manager
    # [19/12/13 11:09:23] Seppia: pid=1432, owner=WIN7-NOAV\avtest, cmd=vmtoolsd.exe
    # pid=1776, owner=NT AUTHORITY\SYSTEM, cmd=vmtoolsd.exe
    # pid=712, owner=NT AUTHORITY\SYSTEM, cmd=TrustedInstaller.exe
    # pid=1376, owner=WIN7-NOAV\avtest, cmd=wuauclt.exe
    # pid=1408, owner=WIN7-NOAV\avtest, cmd=wuauclt.exe
    # [19/12/13 11:09:53] Seppia: questa e' una vm che sta facendo aggiornamento, con i vmwaretools partiti (user logged on)

    user_logged = False
    vm_tools = False
    install = False
    try:
        processes = vm_manager.execute(vm, "list_processes");
    except:
        logging.exception("cannot get processes")
        #processes = vm_manager.execute(vm, "listProcesses");
        #logging.debug("listProcesses: %s" % processes)

    if not processes:
        try:
            sleep(60)
            logging.debug("trying listProcesses")
            procs = vm_manager.execute(vm, "listProcesses");
            if config.verbose:
                logging.debug("listProcesses: %s" % procs)
            processes = helper.convert_processes(procs)
        except:
            logging.exception("listProcesses")

    if not processes:
        return "NOT-STARTED"

    try:
        if config.verbose:
            logging.debug("%s, list_processes: %s" % (vm, [ (p["name"],p["owner"]) for p in processes] ))
        vmtools_number = 0
        for process in processes:
            if process["owner"].endswith("avtest"):
                user_logged = True
                if process["name"] == "vmtoolsd.exe":
                    # owner=WIN7-NOAV\avtest, cmd=VMwareTray.exe
                    vmtools_number += 1
            if process["owner"].endswith("SYSTEM") and process["name"] == "vmtoolsd.exe":
                vmtools_number += 1
            #removed on 05/05/2015 because the win update is no more
            # if process["name"] == "wuauclt.exe" or process["name"] == "TrustedInstaller.exe":
            #     install = True
        if vmtools_number >= 2:
            vm_tools = True
        # explorer, vmware solo se logged in
    except:
        logging.exception("error")

    if vm_tools:
        return "LOGGED-IN"
    if install:
        return "INSTALL"
    if not user_logged:
        return "LOGGED-OFF"
    else:
        return "NO-VM-TOOLS"

def execute(vm, protocol, args):
    """ server side """
    from AVMaster import vm_manager

    #logging.debug("    CS Execute")
    assert vm, "null vm"
    mq = protocol.mq

    if not args:
        args = ""

    check_avagent = ("AV_AGENT" in args)
    no_check = ("NO_CHECK" in args)

    mq.reset_connection(vm)
    ret = vm_manager.execute(vm, "startup")
    started = False
    if not ret:
        return False, "Not Started VM - vsphere cannot start vm"

    max_install = 10
    max_tries = 20

    if no_check:
        for i in range(8):
            sleep(10)
            if vm_manager.execute(vm, "is_powered_on"):
                 return True, "Started VM (no win startup check)"
        return False, "Error Occurred: Timeout while starting VM"

    for i in range(3):
        sleep(10)
        if vm_manager.execute(vm, "is_powered_on"):
            vm_tools_present = None
            for j in range(max_tries):
                vm_tools_present = False
                if mq.check_connection(vm):
                    logging.debug("got connection from %s" % vm)
                    return True, "Started VM (connection to redis OK)"

                for k in range(max_install):
                    status = get_status(vm)
                    logging.debug("%s, got status: %s" % (vm, status))

                    if status == "INSTALL":
                        logging.debug("waiting for the install to finish: %s/%s" % (i, max_install))
                        sleep(60)
                    else:
                        break

                if status == "LOGGED-IN":
                    logging.debug("VM_tools present")
                    vm_tools_present = True
                    logging.debug("%s, executing ipconfig, time: %s/%s" % (vm, j, max_tries))
                    started = vm_manager.execute(vm, "executeCmd", "c:\\windows\\system32\\ipconfig.exe") == 0
                    logging.debug("%s, executed ipconfig, ret: %s" % (vm, started))

                    logging.debug("IP Checking and renewing if necessary")

                    arg = ["/C", 'c:\\windows\\system32\\ipconfig.exe | findstr IP | findstr /l ":\ 10.0. :\ 10.1." || c:\\windows\\system32\\ipconfig.exe /renew']
                    reg = ("c:\\windows\\system32\\cmd.exe", arg, 40, True, True)
                    vm_manager.execute(vm, "executeCmd", *reg)

                    logging.debug("IP Checking completed")

                if started and not check_avagent:
                    return True, "Started VM (no avagent check)"
                else:
                    sleep(30)
            #end for j

            if not started:
                logging.debug("%s: reboot requested" % vm)
                vm_manager.execute(vm, "reboot")
                sleep(60)
                continue

            if vm_tools_present:
                return False, "Not started VM - vsphere started, win started and vmtools is running, but probably avagent does not start or there is a connection problem."
            else:
                return False, "Not started VM - vsphere started, win started, but vmtools are not running"
        else:
            logging.debug("%s: not yet powered" % vm)

    return False, "Error Occurred: Timeout while starting VM"


