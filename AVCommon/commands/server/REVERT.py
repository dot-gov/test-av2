import os
import sys
from AVCommon.logger import logging


def execute(vm, protocol, args):
    """ server side """
    from AVMaster import vm_manager

    #logging.debug("    CS Execute REVERT")
    assert vm, "null vm"

    if args:
        vm_manager.execute(vm, "revert_to_snapshot", args)
    else:
        vm_manager.execute(vm, "revert_last_snapshot")

    return True, "Reverted VM"


