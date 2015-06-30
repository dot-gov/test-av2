import socket
from time import sleep

__author__ = 'fabrizio'

import os
import subprocess
import shutil
import re
import stat

from AVCommon import command
from AVCommon import process
from AVCommon.logger import logging
from AVAgent import build


def on_init(vm, args):
    """ server side """
    puppet =  socket.gethostname()
    args.append( puppet )
    return True


def on_answer(vm, success, answer):
    """ server side """
    from AVMaster import vm_manager
    logging.debug("executing logout")
    #cmd = "/windows/system32/logoff.exe"
    # arg = []
    # ret = vm_manager.execute(vm, "executeCmd", cmd, arg, 40, True, True)
    ret = vm_manager.execute(vm, "pm_run", "logoff", "")
    sleep(2)


def execute_calc():
    logging.debug("executing calc")
    proc = subprocess.Popen(["calc.exe"])
    process.wait_timeout(proc, 20)
    logging.debug("killing calc")
    proc.kill()


def close_instance(puppet, vm):
    try:
        logging.debug("closing instance")
        backend = command.context["backend"]

        build.create_user(puppet, vm, backend)
        build.uninstall(backend)
    except:
        logging.exception("Cannot close instance")


def kill_pid(pid):
    import win32api

    PROCESS_TERMINATE = 1
    handle = win32api.OpenProcess(PROCESS_TERMINATE, False, pid)
    win32api.TerminateProcess(handle, -1)
    win32api.CloseHandle(handle)


def kill_proc_by_regex(procs, reagent):
    exenames = ["%s.exe" % n for n in build.names]

    for caption, pid in [(e['Caption'], int(e['ProcessId'])) for e in procs]:
        if reagent.match(caption) or caption in exenames:
            try:
                logging.debug("WMI %s: %s" % (caption, pid))
                kill_pid(pid)
            except:
                logging.exception("cannot kill pid")


def kill_rcs(vm):
    logging.debug("Killing rcs")

    cmd = 'WMIC PROCESS get Caption,Processid /format:value'
    wmilines = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.readlines()

    procs = []

    for l in wmilines:
        tokens = l.rstrip().split('=')
        if len(tokens) == 2:
            k, v = tokens
            p[k] = v
            if p not in procs:
                procs.append(p)
        else:
            p = {}

    logging.debug("procs: %s" % procs)
    expname = "exp_%s" % vm

    reagent = re.compile(r'agent.*\.exe')
    kill_proc_by_regex(procs, reagent)

    reagent = re.compile(r'.*%s.*\.exe' % expname)
    kill_proc_by_regex(procs, reagent)

    if "notepad" not in build.names:
        build.names.append("notepad")

    for b in build.names:
        subprocess.Popen("taskkill /f /im %s.exe" % b, shell=True)

    tasklist = subprocess.Popen(["tasklist"], stdout=subprocess.PIPE).communicate()[0]
    logging.debug(tasklist)


def delete_startup():
    logging.debug("deleting startup")
    for d in build.start_dirs:
        for b in build.names:
            filename = "%s/%s.exe" % (d, b)
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except:
                    logging.exception("Cannot delete %s" % filename)


def remove_agent_startup():
    start_dirs = ['C:/Users/avtest/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup',
                  'C:/Documents and Settings/avtest/Start Menu/Programs/Startup']
    for startup_dir in start_dirs:
        remote_name = "%s/av_agent.bat" % startup_dir
        if os.path.exists(remote_name):
            os.remove(remote_name)


def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)


def delete_build():
    logging.debug("deleting build")
    try:
        if os.path.exists("build"):
            shutil.rmtree("build", onerror=remove_readonly)
    # if the system cannot delete build...not a so big problem
    except:
        pass


def execute(vm, args):
    #if not args:
    #    args = ""

    puppet = args.pop()

    # execute "calc.exe"
    execute_calc()
    sleep(2)
    # build.close(instance)
    # if not no_clean_instances:
    close_instance(puppet, vm)
    sleep(2)
    # kill process
    kill_rcs(vm)
    sleep(2)
    # delete startup
    delete_startup()
    sleep(2)
    # add avagent.bat to startup
    #remove_agent_startup()
    # sleep 20
    delete_build()
    sleep(2)

    return True, "UNINSTALLED"
