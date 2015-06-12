import os
import sys
from AVCommon.logger import logging


def execute(vm, protocol, args):
    """ server side """
    from AVMaster import vm_manager

    #logging.debug("    CS Execute REVERT")
    assert vm, "null vm"

    if args:
        name = str(args)
        vm_manager.execute(vm, "revert_named_snapshot", name)
        return True, "Reverted VM"
    else:
        #replaced revert_last_snapshot

        if vm_manager.execute(vm, "pm_revert_last_snapshot"):
            return True, "Reverted VM: %s" % vm
        else:
            return False, "Error reverting VM: %s" % vm
