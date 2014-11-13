__author__ = 'fabrizio'

import os
import sys
import glob
from AVCommon.logger import logging
from AVCommon import config
import time
import tempfile

from AVCommon import command

vm = None


def execute(vm, protocol, inst_args):
    from AVMaster import vm_manager

    """ client side, returns (bool,*) """
    logging.debug("    INSTALL_AGENT" )
    mq = protocol.mq

    assert vm, "null vm"
    assert command.context is not None

    failed = False

    if inst_args:
        redis = inst_args
    else:
        redis = config.redis

    cmd = "rmdir /s /q C:\\AVTest\\running \r\n"\
          "cd C:\\AVTest\\AVAgent\r\n" \
          "c:\\python27\\python.exe"
    arg = ["C:\\AVTest\\AVAgent\\av_agent.py", "-m", vm, "-s", mq.session, "-d", redis]
    start_bat = "%s %s\r\n" %( cmd, " ".join(arg) )

    agent_bat = "start /min C:\\AVTest\\AVAgent\\start.bat ^& exit\r\n"

    # --------------av_agent.bat-----------------
    fd, filename = tempfile.mkstemp(".bat")
    logging.debug("opening file %s with fd: %s" % (filename, fd))
    os.write(fd, agent_bat)
    os.close(fd)

    assert os.path.exists(filename)

    startup_dir_7 = 'C:/Users/avtest/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup'
    startup_dir_XP = 'C:/Documents and Settings/avtest/Start Menu/Programs/Startup'

    if vm.endswith("32"):
        startup_dir = startup_dir_XP
    else:
        startup_dir = startup_dir_7

    remote_name = "%s/av_agent.bat" % startup_dir
    remote_name= remote_name.replace("/","\\")
    logging.debug("I'll copy %s" % filename)
    r = vm_manager.execute(vm, "copyFileToGuest", filename, remote_name )
    if r > 0:
        failed = True
        logging.debug("Cannot copy %s to %s" % ( filename, remote_name ))

    os.remove(filename)

    # --------------start.bat-----------------

    fd, filename = tempfile.mkstemp(".bat")
    logging.debug("opening file %s with fd: %s" % (filename, fd))
    os.write(fd, start_bat)
    os.close(fd)
    assert os.path.exists(filename)

    remote_name = "C:\\AVTest\\AVAgent\\start.bat"
    logging.debug("I'll copy %s" % filename)
    r = vm_manager.execute(vm, "copyFileToGuest", filename, remote_name )
    if r > 0:
        failed = True
        logging.debug("Cannot copy %s" % filename)
    os.remove(filename)

    # --------------delete running-----------------
    dirname = "%s/avagent/running" % config.basedir_av
    r = vm_manager.execute(vm, "deleteDirectoryInGuest", dirname)
    if r > 0:
        failed = True
        logging.debug("Cannot delete %s" % dirname)

    # --------------delete logs-----------------
    dirname = "%s/logs" % config.basedir_av
    r = vm_manager.execute(vm, "deleteDirectoryInGuest", dirname)
    if r > 0:
        failed = True
        logging.debug("Cannot delete %s" % dirname)

    if failed:
        return False, "Cant Copy %s on VM" % filename

    else:
        return True, "File copied"
