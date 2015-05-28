# -*- coding: utf-8 -*-
import json

import time
import csv
import os
import traceback
from collections import deque
import datetime
import argparse
import inspect
import sys
import signal
import subprocess
import threading

inspect_getfile = inspect.getfile(inspect.currentframe())
cmd_folder = os.path.split(os.path.realpath(os.path.abspath(inspect_getfile)))[0]
os.chdir(cmd_folder)



# print cmd_folder

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)
parent = os.path.split(cmd_folder)[0]
ancestor = os.path.split(parent)[0]
if parent not in sys.path:
    sys.path.insert(0, parent)
if ancestor not in sys.path:
    sys.path.insert(0, ancestor)
from RiteMobile.Android.commands_device import CommandsDevice
from RiteMobile.Android import adb
from RiteMobile.Android.utils import myprocess

inspect_getfile = inspect.getfile(inspect.currentframe())
cmd_folder = os.path.split(os.path.realpath(os.path.abspath(inspect_getfile)))[0]
os.chdir(cmd_folder)

# print cmd_folder

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)
parent = os.path.split(cmd_folder)[0]
ancestor = os.path.split(parent)[0]
if parent not in sys.path:
    sys.path.insert(0, parent)
if ancestor not in sys.path:
    sys.path.insert(0, ancestor)

#print sys.path
all_tests="all, audio, chat, persistence, photo, root"

def parse_args():
    parser = argparse.ArgumentParser(description='run install and uninstall.')
    parser.add_argument('-d', '--device', required=False,
                        help="choose serial number of the device to use")
    parser.add_argument('-i', '--interactive', required=False, action='store_true',
                        help="ask on which device")
    parser.add_argument('-s', '--specifictest', required=False, default='all', choices=all_tests.split(', '),
                        help="which specific test:  %s" % all_tests)
    args = parser.parse_args()
    return args


def handler(signum, args):
    print "handling signal... %d" % signum
    if signum in [1, 2, 3, 15]:
        print 'Caught signal %s, exiting.' % (str(signum))
        if not main.tr_dequeue:
            kill_all()
        sys.exit()
    else:
        print 'Caught signal %s, ignoring.' % (str(signum))


def add_thread(tr):
    if not main.tr_dequeue:
        main.tr_dequeue = deque()
    main.tr_dequeue.append(tr)


def kill_all():
    if main.tr_dequeue:
        for elem in main.tr_dequeue:  # iterate over the deque's elements
            if type(elem) is myprocess.GenericThread:
                while elem.is_alive_inner():
                    elem.runBaby = False
                print "killed %s" % elem.cmd


def something_running():
    if not main.tr_dequeue:
        return False
    for elem in main.tr_dequeue:  # iterate over the deque's elements
        if type(elem) is myprocess.GenericThread:
            if elem.is_alive_inner():
                return True
    return False


def get_devices_list():
    devices = []
    #devices = ""
    # Find All devices connected via USB
    ret = adb.execute(adb_cmd="devices")
    for line in ret.split('\n'):
        if '\t' in line:
            dev = line.split('\t')[0]
            if dev:
                devices.append(dev)
    return devices


def main():
    main.tr_dequeue = None
    args = parse_args()

    specific = args.specifictest.strip()

    assert specific in all_tests.split(', ')

    if specific == "all":
        specifictest = "test_all.py"
    else:
        specifictest = "test_functional_%s.py" % specific


    catchable = ['SIGINT', 'SIGQUIT', 'SIGHUP', 'SIGTERM']
    for i in catchable:
        signum = getattr(signal, i)
        signal.signal(signum, handler)
    main_cmd = ""
    #for i in sys.argv[1:]:
    #    main_cmd += i + " "

    if not os.path.exists('run'):
        os.mkdir('run')

    if not args.interactive:
        main_cmd = ""
        #for i in sys.argv[1:]:
        #    if i not in "-d" and i not in "-A":
        #        main_cmd += i + " "
        devices = get_devices_list()
        print "devices connessi: %d [%s]\n" % (len(devices), main_cmd)

        for id in range(len(devices)):
            #print "`which python` test_install_root_unistall.py %s -d %s" % (main_cmd, devices[id])
            add_thread(myprocess.GenericThread(
                "`which python` %s %s -d %s %s > run/%s.txt" % (specifictest, main_cmd, devices[id], args.specificargs, devices[id])))
            time.sleep(1)
    else:
        add_thread(myprocess.GenericThread("`which python` %s %s %s" % (specifictest, args.specificargs, main_cmd)))

    time.sleep(2)
    while something_running():
        time.sleep(2)


if __name__ == "__main__":
    main()
