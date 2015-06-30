import os
import sys
from AVCommon.logger import logging
from AVCommon import logger

import time


def execute(vm, protocol, img_path):
    """ server side """
    # TODO: add Proc name
    from AVMaster import vm_manager

    #logging.debug("    CS Execute")
    assert vm, "null vm"

    basedir = "%s/screenshots" % logger.logdir

    if not img_path:
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        img_path = "%s/%s.%s.png" % (basedir, vm, int(time.time()))

    ret = vm_manager.execute(vm, "pm_screenshot", img_path)
    if ret is True:
        #blob = open(img_path).read()
        return ret, img_path
    else:
        return ret, "Screenshot not saved"

