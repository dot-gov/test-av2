__author__ = 'marcol'
from AVCommon.logger import logging


def on_init(protocol, args):
    from AVMaster import vm_manager

    vm, mq = protocol.vm, protocol.mq
    cmd = "taskkill"
    # arg = ["/F", "/IM", "python.exe"]
    # ret = vm_manager.execute(vm, "executeCmd", cmd, arg, 40, True, True)
    ret = vm_manager.execute(vm, "pm_run", cmd, "/F " + " /IM " + " python.exe")

    return True


def on_answer(vm, success, answer):
    """ server side """
    pass


def execute(vm, args):
    """ client side, returns (bool,*) """
    logging.debug("    STOP_AGENT")
    assert vm, "null vm"



    #TODO: stops a AVAgent on vm
    return True, "AGENT STOPPED"