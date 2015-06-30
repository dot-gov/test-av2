import os
import sys
from AVCommon.logger import logging
from AVCommon import config

def execute(vm, protocol, dirname):
    from AVMaster import vm_manager

    #logging.debug("    CS Execute")
    assert vm, "null vm"
    #assert len(args) == 1 and isinstance(args, str), "Argument must be a string."
    assert isinstance(dirname, str), "Argument must be single."

    if not dirname.startswith("/") and not dirname.startswith("\\") and not dirname.startswith("C:"):
        dirname = "%s/%s" %(config.basedir_av, dirname)
    dirname = dirname.replace('/','\\')

    logging.debug("Deleting %s from %s" % (dirname, vm))
    r = vm_manager.execute(vm, "pm_delete_directory", dirname)

    if not os.path.exists(dirname):
        return True, "Directory %s deleted" % dirname
    else:
        return False, "Directory %s not deleted" % dirname