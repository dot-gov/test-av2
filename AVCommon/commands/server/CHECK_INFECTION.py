import os
import sys
from AVCommon.logger import logging
from time import sleep
from operator import xor
from AVAgent import build

def execute(vm, protocol, args):
    from AVMaster import vm_manager

    """ server side """
    clean = True # VM IS NOT INFECTED!! TEST CAN CONTINUE!!!

    #logging.debug("    CS Execute")
    assert vm, "null vm"

    invert = "STOP_IF_CLEAN" in args if args else False

    #blacklist = ['BTHSAmpPalService','CyCpIo','CyHidWin','iSCTsysTray','quickset']

    dirs = ['C:/Users/avtest/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup',
            'C:/Documents and Settings/avtest/Start Menu/Programs/Startup']


    names = build.names[:]
    names.remove("agent")

    #checks scout and soldier
    for d in dirs:
        out = vm_manager.execute(vm, "listDirectoryInGuest", d)
        #logging.debug("listDirectoryInGuest: %s" % out)

        for b in names:
            if b in out:
                logging.info("%s, found %s in %s" % (vm, b, d))
                clean = False
                break

    #checks elite
    out = vm_manager.execute(vm, "listDirectoryInGuest", "c:/")
    if "infe.txt" in out:
        logging.info("%s, ELITE detected: found infe.txt in c:" % vm)
        clean = False

    ret = xor(clean is True, invert)
    if clean is True:
        return ret, "VM is not infected"
    else:
        return ret, "VM is INFECTED"
