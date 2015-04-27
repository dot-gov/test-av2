import os

__author__ = 'mlosito'


from AVCommon.logger import logging
import glob

from AVCommon import command
from AVAgent import build


def on_init(protocol, args):
    return True


def on_answer(vm, success, answer):
    pass


#uses a list of files. No wildcards (or how can I check if they exists?)
def execute(vm, args):
    logging.debug("Checking file existance: %s" % args)
    failed = []
    for file_to_check in args:
        if not os.path.exists(file_to_check):
            failed.append(file_to_check)
            logging.debug("File existance FAILED for file: %s" % file_to_check)
    return failed == [], failed