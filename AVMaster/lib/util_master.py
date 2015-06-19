__author__ = 'mlosito'

import time


#exe is a windows executable with full path (/ or \\) like "c:\\Windows\\System32\\ipconfig.exe"
#args is in the form: ['/c', 'del', remote_name]
def run_agent_exe(vm_manager, vm, exe, args):
    exe = exe.replace("/", "\\")
    cm = (exe, args, 40, True, True)
    vm_manager.execute(vm, "executeCmd", *cm)


#cmd is a cmd.exe command, like del or dir
#args is in the form: ['/c', 'del', remote_name]
def run_agent_cmd(vm_manager, vm, cmd, args):
    arg = ['/c', cmd] + args
    cm = ("c:\\Windows\\System32\\cmd.exe", arg, 40, True, True)
    vm_manager.execute(vm, "executeCmd", *cm)
    time.sleep(2)