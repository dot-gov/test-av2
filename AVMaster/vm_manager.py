import os
import sys
import socket
from AVCommon.logger import logging
from AVCommon import command

sys.path.append(os.path.split(os.getcwd())[0])
sys.path.append(os.getcwd())

from lib.core.VMRun import VMRun
from lib.core.VMachine import VMachine
from lib.core.VMPyvmomi import VMPyvmomi

from AVCommon import config

prev = os.path.join(os.getcwd(), "..")
if not prev in sys.path:
    sys.path.append(prev)

vm_conf_file = "AVMaster/conf/vms-%s.cfg" % socket.gethostname()


def execute(vm_name, cmd, *args):
    global vm_conf_file
    # pysphere, vi_server
    #uses VMachine.py
    vmachine_cmds = ["startup", "shutdown", "reboot",
                     "get_snapshots", "revert_last_snapshot", "revert_to_snapshot", "revert_named_snapshot", "create_snapshot",
                     "delete_snapshot",
                     "is_powered_on", "is_powered_off", "get_status",
                     "list_directory", "make_directory", "get_file", "send_file", "list_processes"]
    # vmware tools
    # uses VMRun.py
    vmrun_cmds = ["executeCmd", "runTest", "takeScreenshot", "listProcesses",
                  "mkdirInGuest", "copyFileToGuest", "copyFileFromGuest", "deleteDirectoryInGuest",
                  "listDirectoryInGuest", "refreshSnapshot"]

    pyvmomi_cmds = ["pm_poweron", "pm_poweron_and_check", "pm_poweroff", "pm_list_directory", "pm_put_file", "pm_get_file", "pm_run_and_wait",
                    "pm_run", "pm_ip_addresses", "pm_revert_last_snapshot"]

    if config.verbose:
        logging.debug("vm: %s, command: %s" % (vm_name, cmd))

    try:
        vm = VMachine(vm_name)
        vm.get_params(vm_conf_file)

        if command.context is not None:
            vm.user = command.context.get("USERNAME", vm.user)
            vm.passwd = command.context.get("PASSWORD", vm.user)

        #logging.debug("USER: %s, PASSDW: %s" % (vm.user, vm.passwd))
        assert vm.config

        if cmd in vmrun_cmds:
            vmrun = VMRun(vm_conf_file)
            f = getattr(vmrun, cmd)
            if not args:
                return f(vm)
            else:
                return f(vm, *args)

        elif cmd in vmachine_cmds:
            f = getattr(vm, cmd)
            if not args:
                return f()
            else:
                return f(args)
        elif cmd in pyvmomi_cmds:
            with VMPyvmomi(vm_conf_file, vm_name) as pyvv:
                f = getattr(pyvv, cmd)
                if not args:
                    return f()
                else:
                    return f(args)
        else:
            logging.error("command not found: %s" % cmd)
            raise Exception("Command not found")
    except AssertionError as ae:
        logging.error("Assertion found: %s" % ae)
        raise
    except Exception as e:
        logging.error("Exception found. %s" % e)
        raise


if __name__ == '__main__':

    logging.debug("args: %s" % str(sys.argv[1:]))
    t = tuple(sys.argv[1:])
    ret = execute(*t)

    logging.info(ret)
