__author__ = 'zeno'

from AVCommon.logger import logging
import time
import glob

from AVCommon import command
from AVAgent import build

# debug = True


def on_init(protocol, args):
    return True


def on_answer(vm, success, answer):
    pass

#the scan needs one list of files, and does not support wildcards and directories
def execute(vm, args):
    logging.debug("Checking files: %s" % args)
    # if not debug:
    #     files = [glob.glob(f) for f in args]
    #     if [] in files:
    #         return False, "All files were detected. Found files: " + str(files)
    #     flat = [item for sublist in files for item in sublist]
    #     logging.debug("files: %s, expanded files: %s" % (files, flat))
    # else:
    #     #for debug I need to execute check static even if the files were already removed by AV.
    #     flat = args

    failed = build.check_static_scan(args, vm, report=command.context["report"])
    logging.debug("DEBUG - build.check_static_scan. Detected files:: %s", failed)
    return failed==[], failed