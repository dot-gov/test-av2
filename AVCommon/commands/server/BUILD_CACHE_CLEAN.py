import shutil
import os

from AVCommon.logger import logging
from datetime import date

def execute(vm, protocol, keep_samples):

    src = 'build_cache'
    dst = 'logs/samples_%s/' % str(date.today())

    """ server side """
    #default: does not saves samples
    if not isinstance(keep_samples, bool):
        keep_samples = False

    if keep_samples:
        logging.debug("Moving samples to logs")
        if not os.path.exists(src):
            return True, "No cache to keep!"

        if not os.path.exists(dst):
            os.makedirs(dst)
        files = os.listdir(src)
        for f in files:
            logging.debug("Moving %s" % os.path.join(src, f))
            shutil.move(os.path.join(src, f), os.path.join(dst, f))
    #I delete anyway the dir
    try:
        if os.path.exists(src):
            shutil.rmtree(src)
    except:
        return False, "Error cleaning cache!"

    return True, "Cache cleaned"

