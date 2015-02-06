import os
from time import sleep
import glob
from AVCommon.logger import logging
from AVCommon import config

report_level = 2


def execute(vm, protocol, args):
    """ server side """
    from AVMaster import vm_manager

    logging.debug("    CS PUSH: %s" % str(args))
    assert vm, "null self.vm"
    assert isinstance(args, list)

    if isinstance(args[0], list):
        src_files, src_dir, dst_dir = args
        explicit = True
    elif isinstance(args[0], basestring):
        src_files, src_dir, dst_dir = args, config.basedir_server, config.basedir_av
        explicit = False
    else:
        raise RuntimeError("wrong arguments")

    assert isinstance(src_files, list), "PUSH expects a list of src files"

    all_src = []
    relative_parents = set()

    """ look if i need all files in one directory """
    for src_file in src_files:
        g = glob.glob(os.path.join(src_dir, src_file))
        if not g:
            logging.warn("Empty glob")

        logging.debug("    file: %s" % str(g))
        # if you arrive here, then you already found the file on the filesystem.
        # typically the file have a relative path
        for f in g:
            # s is the relative file, expanded by glob
            s = f.replace("%s/" % src_dir, "")
            all_src.append(s)
            #logging.debug("file completo f: %s, file relativo s: %s" % (f,s))

            #logging.debug("Check if exists file %s" % f)
            assert os.path.exists(f), "%s %s" % (f, os.getcwd())

            #inserito da Marco
            #logging.debug("Check if exists file %s" % os.path.join(src_dir, s))
            assert os.path.exists(os.path.join(src_dir, s)), "%s %s" % (s, os.getcwd())

            # add all the parents to the relative_parents set, to avoid repetitions
            p = os.path.split(s)[0]
            while p and p != src_dir and p != "/":
                logging.debug("    p: %s" % str(p))
                relative_parents.add(p)
                #print("1_relative parents")
                p = os.path.split(p)[0]

    # sorts the parents by length, so that parent is always before its sons

    relative_parents.add("./")
    parents = list(relative_parents)
    parents.sort(lambda x, y: len(x) - len(y))
    logging.debug("parents: %s" % parents)

    ntdir = lambda x: x.replace("/", "\\")

    print(parents)

    for r in parents:
        #print(dst_dir)
        rdir = ntdir(os.path.join(dst_dir, r))
        #print("2_crea cartelle %s" % rdir)
        logging.debug("mkdir %s " % (rdir))
        vm_manager.execute(vm, "mkdirInGuest", rdir)

    """ then upload parsed files """
    logging.debug("All files to copy are:\n%s" % src_files)
    if not all_src:
        return False, "Empty file list"

    for src_file in all_src:
        #print("3_processa file")
        src = os.path.join(src_dir, src_file)
        dst = ntdir(os.path.join(dst_dir, src_file))

        #logging.debug("Check if exists file %s" % src)

        if not os.path.exists(src):
            return False, "Not existent file: %s" % src
        else:
            pass
            #logging.debug("file exists")

        logging.debug("%s copy %s -> %s" % (vm, src, dst))
        r = vm_manager.execute(vm, "copyFileToGuest", src, dst)
        sleep(10)
        if r > 0:
            return False, "Cant Copy %s on VM" % src_file

    return True, "Files copied on VM"

