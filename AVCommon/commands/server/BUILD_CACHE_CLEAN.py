import shutil
import os

from AVCommon.logger import logging
from datetime import date

def execute(vm, protocol, keep_samples):

    src = 'build_cache'
    dst = 'logs/samples_%s/' % str(date.today())

    """ server side """
    #default: CLEAN samples
    #default: if True, then save samples without deleting them!!!
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
        # TEMPORANEAMENTE DISABILITATA COPIA MULTIPLA (che non funziona perche' avviene per ogni VM)
        #    i = 0
            dst_full_file_name = os.path.join(dst, f)
        #    while os.path.exists(dst_full_file_name):
        #        i += 1
        #        dst_full_file_name = "%s_new_%s.zip" % (os.path.join(dst, f), i)

            logging.debug("Moving %s to %s" % (os.path.join(src, f), dst_full_file_name))
        #    shutil.move(os.path.join(src, f), dst_full_file_name)
            if not os.path.exists(dst_full_file_name):
                shutil.copy(os.path.join(src, f), dst_full_file_name)
    #if not keep_samples
    else:
        try:
            if os.path.exists(src):
                shutil.rmtree(src)
        except:
            return False, "Error cleaning cache!"

    return True, "Cache cleaned"

