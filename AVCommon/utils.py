__author__ = 'mlosito'

import os
import ntpath
import glob
import zipfile
import tempfile
import shutil
from time import sleep
from AVCommon.logger import logging
from AVCommon import config



def unzip(filename, fdir, logging_function):
    zfile = zipfile.ZipFile(filename)
    names = []
    for name in zfile.namelist():
        if os.path.exists(name):
            os.remove(name)
        (dirname, filename) = os.path.split(name)
        logging_function("- Decompress: %s / %s" % (fdir, filename))
        zfile.extract(name, fdir)
        names.append(os.path.join(fdir, name))
    return names


def pushzip(vm, args):
    """ server side """
    from AVMaster import vm_manager

    logging.debug("    CS PUSHZIP: %s" % str(args))
    assert vm, "null self.vm"
    assert isinstance(args, list)

    retry = 1  # (tries one time)

    #if first argument is the number of retries, then I use all the remaining elements as filenames and continue
    if isinstance(args[0], int):
        retry = args[0] + 1  # (tries n+ 1 time)
        args = args[1:]

    if isinstance(args[0], basestring):
        src_files, src_dir, dst_dir = args, config.basedir_server, config.basedir_av
    else:
        raise RuntimeError("wrong arguments")

    assert isinstance(src_files, list), "PUSHZIP expects a list of src files"

    all_src = []

    """ look if i need all files in one directory """
    for src_file in src_files:
        g = glob.glob(os.path.join(src_dir, src_file))
        if not g:
            logging.warn("Empty glob")
        # if you arrive here, then you already found the file on the filesystem.
        # typically the file have a relative path
        for f in g:
            # s is the relative file, expanded by glob
            s = f.replace("%s/" % src_dir, "")
            all_src.append(s)

            #logging.debug("Check if exists file %s" % f)
            assert os.path.exists(f), "%s %s" % (f, os.getcwd())

            #inserito da Marco
            #logging.debug("Check if exists file %s" % os.path.join(src_dir, s))
            assert os.path.exists(os.path.join(src_dir, s)), "%s %s" % (s, os.getcwd())

    ntdir = lambda x: x.replace("/", "\\")

    print 'creating archive'
    d = tempfile.mkdtemp()
    zfname = d + '/zipfile_write.zip'
    zf = zipfile.ZipFile(zfname, mode='w')
    pwd = config.basedir_server

    #adding files to zip!
    logging.debug("All files to copy are:\n%s" % src_files)

    if not all_src:
        return False, "Empty file list"

    for src_file in all_src:
        #print("3_process a file")
        src = os.path.join(src_dir, src_file)

        #logging.debug("Check if exists file %s" % src)
        if not os.path.exists(src):
            return False, "Not existent file: %s" % src
        else:
            pass

        logging.debug("%s adding %s -> %s" % (vm, src, src_file))
        zf.write(src_file)

    zf.close()
    #zip file is ready

    file_number = len(all_src)

    #just to be sure we wait the zipfile creation
    for ret in range(0, 10):
        if os.path.exists(zfname):
            break
        sleep(6)

    not_copyed = []
    #tries n times to upload and extract all files, with increasing delays
    for tr in range(0, retry):
        logging.debug("tries n times to upload and extract all files, with increasing delays, try %s of %s" % (tr + 1, retry))

        vm_manager.execute(vm, "mkdirInGuest", ntdir(dst_dir))
        sleep(tr)
        # copy unzip (it should be already in AVAgent/assets...)
        unzipexe = "assets/unzip.exe"
        dst = ntdir(os.path.join(dst_dir, "unzip.exe"))

        logging.debug("Copy unzip: %s -> %s" % (unzipexe, dst))
        vm_manager.execute(vm, "pm_put_file", unzipexe, dst)
        sleep(2 * tr)

        tmpzip = "tmp.zip"
        dst = ntdir(os.path.join(dst_dir, tmpzip))
        logging.debug("Copy zip: %s -> %s" % (zfname, dst))
        vm_manager.execute(vm, "pm_put_file", zfname, dst)
        sleep(2 * tr)

        logging.debug("Executing unzip on %s" % dst)
        # unzipargs = ("/AVTest/unzip.exe", ["-o", "-d", "c:\\avtest", dst], 40, True, True)
        # ret = vm_manager.execute(vm, "executeCmd", *unzipargs)

        ret = vm_manager.execute(vm, "pm_run_and_wait", "/AVTest/unzip.exe", "-o -d c:\\avtest %s" % dst)
        # logging.debug("ret: %s" % ret)
        # #sleep(3 * tr)
        # sleep(5 * tr + file_number)
        not_copyed = []
        #if there are retries I check the existance of files and if are all present, I terminate the iteration
        if retry > 1:
            logging.debug("Checking if the files were been copyed and extracted correctly. Files: %s", all_src)
            failed = False
            dirs = get_all_dirs(all_src)
            found_files = list_all_files_in_dirs(vm, vm_manager, dirs)
            to_check_files = get_remote_filenames(all_src)
            for file_to_check in to_check_files:
                if file_to_check not in found_files:
                    logging.debug("NOT FOUND: %s" % file_to_check)
                    failed = True
                    not_copyed.append(file_to_check)
            if not failed:
                shutil.rmtree(d)
                return True, "Files copied on VM"
        tr += 1

    logging.debug("Removing zip: %s" % d)
    shutil.rmtree(d)

    if retry > 1:
        #if I'm here and retries were executed, then I have an error
        return False, "Impossible to copy all files on VM (not copyed: %s)" % str(not_copyed)
    else:
        #if no retries, we always return true
        return True, "Tried one file copy (no check) on VM"


def get_remote_filenames(all_src):
    remote_files = []
    for file_to_convert in all_src:
        if not file_to_convert.startswith("\\") and not file_to_convert.startswith("/"):
            file_to_convert = "\\" + file_to_convert
        remote_file = config.basedir_av + file_to_convert
        remote_files.append(remote_file.replace("/", "\\"))
    return remote_files


def get_all_dirs(all_src):
    all_dir = set()
    for file_to_check in all_src:
        dir_to_check = ntpath.dirname(file_to_check.replace("/", "\\"))  # rimuovi tutto quello che c'e' dopo l'ultima /
        # print "all_dirs_to_check -> " + dir_to_check
        if dir_to_check == "":
            dir_remota = config.basedir_av
        else:
            dir_remota = config.basedir_av + "\\" + dir_to_check
        # print "all_dirs_to_list -> " + dir_remota.replace("/", "\\")
        all_dir.add(dir_remota.replace("/", "\\"))
    return all_dir


def list_all_files_in_dirs(vm, vm_manager, dirs):
    files = []
    logging.debug(dirs)
    for d in dirs:
        #list_directory
        #string_out = vm_manager.execute(vm, "list_directory", d+"\\")
        list_out = vm_manager.execute(vm, "pm_list_directory", d)
        if not len(list_out):
            logging.debug("Dir: %s -> Empty directory!" % d)
        else:
            logging.debug("Dir: %s -> %s" % (d, list_out))
            for filename in list_out:  # .split("\n")[1:-1]:
                files.append(d + "\\" + filename)

    logging.debug("All files listed: %s" % files)
    return files