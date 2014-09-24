import os
import sys
from AVCommon.logger import logging


def execute(vm, protocol, args):
    """ server side """

    from AVMaster import vm_manager

    logging.debug("    CS Execute CREATE SNAPSHOT")
    assert vm, "null vm"

    # TODO: check
    vm_manager.execute(vm, "create_snapshot", args)
    return True, "Snapshot refreshed for VM"

