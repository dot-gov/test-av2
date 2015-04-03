__author__ = 'zeno'

from AVCommon.logger import logging
import time
import glob

from AVCommon import command
from AVAgent import build


def on_init(protocol, args):
    return True


def on_answer(vm, success, answer):
    pass


def execute(vm, args):
    logging.debug("Checking files: %s" % args)
    files = [ glob.glob(f) for f in args ]
    if [] in files:
        return False, files

    flat = [ item for sublist in files for item in sublist ]
    logging.debug("files: %s, expanded files: %s" % (files, flat))
    failed = build.check_static(flat, command.context["report"])
    logging.debug("DEBUG - result from build.check_static: %s", failed)
    return failed==[], failed