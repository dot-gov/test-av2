import os
import sys
from AVCommon.logger import logging
from time import sleep
from operator import xor
from AVAgent import build
from AVCommon import logger

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
        logging.debug("listDirectoryInGuest: %s" % out)

        for b in names:
            if b in out:
                logging.info("%s, found %s in %s" % (vm, b, d))
                clean = False
                break

    #checks elite
    # out = vm_manager.execute(vm, "listDirectoryInGuest", "C:/Python27/")
    # if "inf.txt" in out:
    #     logging.info("%s, ELITE detected: found infe.txt in c:" % vm)
    #     clean = False

    #experimental reg query startup for Elite

    reg_file = "c:\\AVTest\\logs\\reg.reg"

    logging.info("%s, Creating reg file" % vm)

    arg = ["EXPORT", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run", reg_file, "/y"]
    reg = ("c:\\Windows\\System32\\reg.exe", arg, 40, True, True)

    ret = vm_manager.execute(vm, "executeCmd", *reg)

    #does not works
    # if ret == 0:
    #     logging.info("Registry saved to: %s executed" % reg_file)
    # else:
    #     logging.exception("Registry saving FAILED")

    dst_dir = logger.logdir

    try:
        src = "c:\\AVTest\\logs\\reg.reg"

        # if not os.path.exists(dst_dir):
        #     os.makedirs(dst_dir)
        # dst_file = "%s/%s/" % (dst_dir, vm)
        dst_file = os.path.join(dst_dir, "%s.reg" % vm)
        # if os.path.exists(dst_file):
        #     os.unlink(dst_file)
            
        logging.debug("PULL: %s -> %s" % (src, dst_file))
        vm_manager.execute(vm, "copyFileFromGuest", src, dst_file)

        with open(dst_file, "r") as f:
            reg_allfile = f.read().decode("utf-16le")
        for key in reg_allfile.splitlines()[2:]:
            logging.debug("reg keys: --%s--" % key)
            # if key == "":
            #     logging.info("skipping empty line")
            #     continue
            if key.find("hex") >= 0:
                logging.info("%s, possible autorun executable detected: found register keyZ --%s-- " % (vm, key))
                if not ".exe" in key and not ".bat" in key:
                    logging.info("%s, ELITE detected: found register keyZ --%s-- " % (vm, repr(key)))
                    clean = False
                    break
    except:
        logging.exception("Cannot get registry file")


    ret = xor(clean is True, invert)
    if clean is True:
        return ret, "VM is not infected"
    else:
        return ret, "VM is INFECTED"
