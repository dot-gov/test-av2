import os
import sys
from AVCommon.logger import logging


def execute(vm, protocol, args):
    """ server side """
    from AVMaster import vm_manager

    #logging.debug("    CS Execute")
    assert vm, "null vm"

    if isinstance(args, list):
        cmd = str(args[0])
        string_args = str(args[1])
        timeout = int(args[2])
        # cmd_args = tuple(args)
        ret = vm_manager.execute(vm, "pm_run_and_wait", cmd, string_args, timeout)
    else:
        cmd = args
        ret = vm_manager.execute(vm, "pm_run_and_wait", cmd, "")
    # ret = vm_manager.execute(vm, "executeCmd", *cmd_args)



    logging.debug("ret: %s" % ret)
    if ret:
        return True, "Command %s executed" % args
    else:
        return True, "Command %s not executed" % args


