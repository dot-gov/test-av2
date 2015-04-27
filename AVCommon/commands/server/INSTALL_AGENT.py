from AVMaster.lib import util_master

__author__ = 'fabrizio'

import os
import re
from AVCommon.logger import logging
from AVCommon import config
import time
import tempfile

from AVCommon import command
import DELETE_DIR
import PUSHZIP
import PULL

vm = None


def execute(vm, protocol, inst_args):
    from AVMaster import vm_manager

    """ client side, returns (bool,*) """
    logging.debug("    INSTALL_AGENT")
    mq = protocol.mq

    assert vm, "null vm"
    assert command.context is not None

    failed = False
    reason = ""

    force_push = False
    redis = config.redis

    if inst_args:
        if isinstance(inst_args, list):
            force_push_str = inst_args[0]
            if len(inst_args) > 1:
                redis = inst_args[1]
        elif isinstance(inst_args, str):
            force_push_str = inst_args
        else:
            return False, "Wrong arguments"

        if force_push_str == "FORCE_PUSH":
            force_push = True
        elif force_push_str == "NO_FORCE_PUSH":
            force_push = False
        else:
            redis = force_push_str

            # if inst_args:
            #     redis = inst_args
            # else:
    #check if here is something to be pushed
    #.py, .yaml, .exe, .json

    matches = []
    for root, dirnames, filenames in os.walk('./'):
        for filename in filenames:
            if re.match('.*\.py|.*\.yaml|.*\.exe|.*\.json', filename):  # fnmatch.filter(filenames, '*.c') or filename in fnmatch.filter(filenames, '*.c') or filename in fnmatch.filter(filenames, '*.c'):
                matches.append(os.path.join(root, filename))

    matches.sort(key=lambda fil: os.stat(fil).st_mtime)

    last_edit_time = os.stat(matches[-1]).st_mtime

    logging.debug("Last edit time: %s (last edited file: %s)" % (last_edit_time, matches[-1]))

    timestamplocalfile = open("timestamp.txt", 'w')
    timestamplocalfile.write(str(last_edit_time))
    timestamplocalfile.close()

    PULL.execute(vm, protocol, [['timestamp.txt'], "c:\\AVTest\\", "logs"])

    if os.path.exists("logs/%s/timestamp.txt" % vm):
        timestampremotefile = open("logs/%s/timestamp.txt" % vm, 'r')
        try:
            timestampremoteint = float(timestampremotefile.read())
        except:
            #if cannot convert, set at 0 and push anyway
            timestampremoteint = 0
        timestampremotefile.close()
        logging.debug("Last edit REMOTE time: %s" % timestampremoteint)
    else:
        timestampremoteint = 0
        logging.debug("Last edit REMOTE unknown: pushing AVAgent anyway.")

    if timestampremoteint < last_edit_time:
        logging.debug("New AVAgent version available. Pushing it.")
    elif force_push:
        logging.debug("Forced push of AVAgent.")
    else:
        return True, "No need to install AVAgent. Skipping."
    # I need to emulate these commands
    # - DELETE_DIR: /AVTest/
    # - DELETE_DIR: /Users/avtest/Desktop/AVTest/
    # - PUSHZIP: [ AVAgent/*.py, AVAgent/*.yaml, AVCommon/*.py, AVCommon/*.yml, AVCommon/commands/client/*.py, AVCommon/commands/meta/*.py, AVCommon/commands/*.py, AVAgent/assets/config*, AVAgent/assets/keyinject.exe, AVAgent/assets/getusertime.exe, AVAgent/assets/windows/*  ]

    #deleteDirectoryInGuest
    DELETE_DIR.execute(vm, protocol, "/AVTest/")
    #not more useful
    #DELETE_DIR.execute(vm, protocol, "/Users/avtest/Desktop/AVTest/")

    zip_success, zip_reason = PUSHZIP.execute(vm, protocol, ["timestamp.txt", "AVAgent/*.py", "AVAgent/*.yaml", "AVCommon/*.py", "AVCommon/*.yaml", "AVCommon/commands/client/*.py", "AVCommon/commands/meta/*.py", "AVCommon/commands/*.py", "AVAgent/assets/config*", "AVAgent/assets/keyinject.exe", "AVAgent/assets/exec_zip.exe", "AVAgent/assets/getusertime.exe", "AVAgent/assets/windows/*"])

    cmd = "rmdir /s /q C:\\AVTest\\running \r\n" \
          "cd C:\\AVTest\\AVAgent\r\n" \
          "c:\\python27\\python.exe"
    arg = ["C:\\AVTest\\AVAgent\\av_agent.py", "-m", vm, "-s", mq.session, "-d", redis]
    start_bat = "%s %s\r\n" % (cmd, " ".join(arg))

    agent_bat = "start /min C:\\AVTest\\AVAgent\\start.bat ^& exit\r\n"

    # --------------av_agent.bat-----------------
    fd, filename = tempfile.mkstemp(".bat")
    logging.debug("Creation of av_agent.bat \nOpening file %s with fd: %s" % (filename, fd))
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
    remote_name = remote_name.replace("/", "\\")

    delete_startup_av_agent(vm_manager, vm, remote_name)

    for i in range(1, 4):
        logging.debug("I'll copy %s (try %s of 3)" % (filename, i))
        assert os.path.exists(filename)
        r = vm_manager.execute(vm, "copyFileToGuest", filename, remote_name)
        if r > 0:
            time.sleep(i * 5)
            failed = True
            reason = "Can't copy av_agent.bat in Startup"
            logging.debug("Cannot copy %s" % filename)
        else:
            failed = False
            reason = ""
            break

    if failed:
        logging.debug("Cannot copy %s: ERROR!" % filename)

    time.sleep(15)

    os.remove(filename)

    #--------------------------------------------
    # NB: WE ARE IGNORING START.BAT COPY ERRORS
    # --------------start.bat-----------------

    fd, filename = tempfile.mkstemp(".bat")
    logging.debug("Creation of start.bat \nOpening file %s with fd: %s" % (filename, fd))
    os.write(fd, start_bat)
    os.close(fd)
    assert os.path.exists(filename)

    remote_name = "C:\\AVTest\\AVAgent\\start.bat"

    for i in range(1, 4):
        logging.debug("I'll copy %s (try %s of 3)" % (filename, i))
        assert os.path.exists(filename)
        r = vm_manager.execute(vm, "copyFileToGuest", filename, remote_name)
        if r > 0:
            time.sleep(i * 5)
            # failed = True
            # reason += "Can't copy start.bat in AVAgent (try %s)" % i
            logging.debug("Cannot copy %s" % filename)
        else:
            # failed = False
            break

    time.sleep(15)

    # if failed:
    #     logging.debug("Cannot copy %s: ERROR!" % filename)

    os.remove(filename)

    # --------------delete running-----------------
    logging.debug("Deleting 'running' dir (if not present, will print 'Error: A file was not found' but is ok")
    dirname = "%s/avagent/running" % config.basedir_av
    r = vm_manager.execute(vm, "deleteDirectoryInGuest", dirname)
    if r > 0:
        failed = True
        reason += " - Cannot delete running file"
        logging.debug("Cannot delete %s" % dirname)

    # --------------delete logs-----------------
    logging.debug("Deleting 'logs' dir (if not present, will print 'Error: A file was not found' but is ok")
    dirname = "%s/logs" % config.basedir_av
    r = vm_manager.execute(vm, "deleteDirectoryInGuest", dirname)
    if r > 0:
        failed = True
        reason += " - Can't delete logs"
        logging.debug("Cannot delete %s" % dirname)

    if failed or not zip_success:
        return False, "Cannot Install Agent on VM. Reason = %s" % (reason + " - " + zip_reason)
    else:
        return True, "Agent installed on VM"


def delete_startup_av_agent(vm_manager, vm, remote_name):
    util_master.run_agent_cmd(vm_manager, vm, "del", [remote_name])
    # arg = ['/c', 'del', remote_name]
    # cm = ("c:\\Windows\\System32\\cmd.exe", arg, 40, True, True)
    # vm_manager.execute(vm, "executeCmd", *cm)