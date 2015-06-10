import os
import sys
from AVCommon.logger import logging
from AVCommon import config

def execute(vm, protocol, args):
    """ server side """
    from AVMaster import vm_manager

    #logging.debug("    CS Execute")
    assert vm, "null vm"
    assert len(args) == 3 and isinstance(args, list), "PULL expects a list of 3 elements"

    #TODO pull files from vm
    src_files, src_dir, dst_dir = args
    assert isinstance(src_files, list), "PULL expects a list of src files"

    if not (src_dir.startswith("\\") or src_dir.startswith("/") or src_dir[1]==':'):
        src_dir = "%s/%s" % (config.basedir_av, src_dir)
        logging.debug("Added basedir to src_dir: %s" % src_dir)

    memo = []
    for src_file in src_files:
        print src_file
        try:
            d, f = src_file.split("\\")
        except ValueError:
            d = ""
            f = src_file

        src = "%s\\%s\\%s" % (src_dir, d, f)
        src = src.replace('/','\\')

        if d == "":
            dst = "%s/%s/%s" % (dst_dir, vm, f)
        else:
            dst = "%s/%s/%s/%s" % (dst_dir, vm, d, f)

        rdir = "%s/%s/%s" % (dst_dir, vm, d)
        if not rdir in memo:
            if not os.path.exists(rdir):
                logging.debug("mkdir %s " % (rdir))
                os.mkdir(rdir)
                memo.append(rdir)

        logging.debug("%s copy %s -> %s" % (vm, src, dst))
        # copyFileFromGuest was replaced
        vm_manager.execute(vm, "pm_get_file", src, dst)

    return True, "Files copied from VM"
