__author__ = 'zeno'

from AVCommon.logger import logging
import socket, time

from AVCommon import command
from AVCommon import build_common
from AVCommon import helper
from AVCommon import utils

from AVAgent import build

def execute(vm, protocol, args):
    from AVMaster import vm_manager
    #build_common.create_user("avmonitor_buildsrv", build_common.connection.DEFAULT[1])

    with build_common.connection() as c:
       f =  c.all_factories()
       logging.debug("ALL FACTORIES: " +  str(f))
       #time.sleep(10)
       return True, str(f)

    return False,"Error"
