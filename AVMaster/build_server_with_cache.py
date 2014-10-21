__author__ = 'mlosito'

import sys
from AVCommon import build_common
from AVCommon.logger import logging

from AVMaster import vm_manager


#TODO: THIS FILE IS MOSTLY EMPTY: remove it!


sys.path.append("/Users/olli/Documents/work/AVTest/")
sys.path.append("/Users/mlosito/Sviluppo/Rite/")
sys.path.append("/Users/zeno/AVTest/")


#pushes the file to client, to be executed
def push_file(vm, exefilename):
    remote_name = "C:\\AVTest\\AVAgent\\buildsrv.exe"
    vm_manager.execute(vm, "copyFileToGuest", exefilename, remote_name)
    logging.debug("Pushed file: %s to: %s" % (exefilename, remote_name))
