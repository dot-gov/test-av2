import os
import sys
from AVCommon.logger import logging
from time import sleep
from operator import xor
from AVAgent import build
from AVCommon import logger
from AVCommon import process
from AVMaster import vm_manager
import subprocess

def execute(vm, protocol, args):
    """ server side """
    assert vm, "null vm"

    invert = "STOP_IF_CLEAN" in args if args else False

    # Tries the first time to check infection
    clean = check_all(vm)
    if not clean:
        for i in range(4):
            relog(vm)
            #aspetto 6 minuti, 1 per il relog e 5 per la sync
            sleep(360)
            #trigger mouse
            trigger_mouse(vm)
            #recheck
            clean = check_all(vm)
            if clean:
                break

    ret = xor(clean is True, invert)
    if clean is True:
        return ret, "VM is not infected"
    else:
        return ret, "VM is INFECTED"


def check_all(vm):
    #checking startup
    clean_soldier_scout = check_scout_soldier(vm)
    logging.info("%s, now I check scout/soldier!" % vm)
    #I run check_elite only if vm is not infected
    if clean_soldier_scout:
        #checking reg
        logging.info("%s, SCOUT/SOLDIER clean!" % vm)
        logging.info("%s, now I check elite!" % vm)
        clean_elite = check_elite(vm)
        if clean_soldier_scout and clean_elite:
            logging.info("%s, VM CLEAN!" % vm)
            clean = True
        else:
            logging.info("%s, ELITE detected" % vm)
            clean = False
    else:
        logging.info("%s, SCOUT/SOLDIER detected" % vm)
        clean = False

    return clean


def trigger_mouse(vm):
    vm_manager.execute(vm, "executeCmd", "c:\\AVTest\\AVAgent\\assets\\keyinject.exe", [], 1, True, True)


def check_elite(vm):
    clean = True
    # checks elite
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
    #wait reg creation
    sleep(15)
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

        sleep(5)

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
    return clean


def check_scout_soldier(vm):
    clean = True
    dirs = ['C:/Users/avtest/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup',
            'C:/Documents and Settings/avtest/Start Menu/Programs/Startup']

    names = build.names[:]
    names.remove("agent")

    # checks scout and soldier
    for d in dirs:
        out = vm_manager.execute(vm, "listDirectoryInGuest", d)
        logging.debug("listDirectoryInGuest: %s" % out)

        for b in names:
            if b in out:
                logging.info("%s, found %s in %s" % (vm, b, d))
                clean = False
                break

    return clean


def relog(vm):
    cmd = "/Windows/System32/logoff.exe"
    ret = vm_manager.execute(vm, "executeCmd", cmd, [], 10, True, True)
    logging.debug("logoff ret: %s" % ret)
