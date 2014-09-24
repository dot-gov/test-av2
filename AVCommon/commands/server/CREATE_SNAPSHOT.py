import os
import sys
from AVCommon.logger import logging


def execute(vm, protocol, args):
    """ server side """

    from AVMaster import vm_manager

    logging.debug("    CS Execute CREATE SNAPSHOT")
    assert vm, "null vm"

    # TODO: check
    name = str(args)
    vm_manager.execute(vm, "create_snapshot", name)
    return True, "Snapshot refreshed for VM"

