__author__ = 'fabrizio'


import os
import sys
from AVCommon.logger import logging
from time import sleep
from AVCommon import mq

def execute(vm, protocol, args):
    """ server side """
    from AVMaster import vm_manager

    #logging.debug("    CS Execute")
    assert vm, "null vm"
    mq = protocol.mq

    #2 minuti e mezzo. Qualche volta windows e' assai lento (per gli update o se viene spento senza preavviso o manca la licenza)
    timeout = 18  #9 = 90 sec; 30 = 300 sec
    if args:
        timeout = args / 10

    mq.reset_connection(vm)

    cmd = "/Windows/System32/logoff.exe"
    # ret = vm_manager.execute(vm, "executeCmd", cmd, [], 10, True, True)
    ret = vm_manager.execute(vm, "pm_run", cmd, "")
    logging.debug("logoff ret: %s" % ret)

    started = False

    #this relog DOES NOT RESTART THE VM. NEVER. If it won't work we should add that feature
    if ret:
        #this is a cycle for the restart (which current implementation doesn't do)
        for i in range(1):
            if vm_manager.execute(vm, "pm_is_powered_on"):
                if vm_manager.execute(vm, "pm_check_login"):
                    return True, "Login VM"
            else:
                return False, "Cannot relogin"
            #
            # else:
            #     logging.debug("%s: powered on" % vm)
            #     for j in range(timeout):
            #         if mq.check_connection(vm):
            #             logging.debug("got connection from %s" % vm)
            #             return True, "Login VM"
            #         sleep(10)
            #
            #     logging.debug("%s: try to reboot" % vm)
            #     ret = vm_manager.execute(vm, "reboot")
            #     sleep(120)
            # else:
            #     sleep(20)


    return False, "Cannot relogin"