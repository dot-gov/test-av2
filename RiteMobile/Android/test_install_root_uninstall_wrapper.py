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

#print cmd_folder

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)
parent = os.path.split(cmd_folder)[0]
ancestor = os.path.split(parent)[0]
if parent not in sys.path:
    sys.path.insert(0, parent)
if ancestor not in sys.path:
    sys.path.insert(0, ancestor)

#print sys.path


def parse_args():
    parser = argparse.ArgumentParser(description='run install and uninstall.')
    parser.add_argument('-a', '--apk', required=True,
                        help="apk to use")
    parser.add_argument('-d', '--device', required=False,
                        help="choose serial number of the device to use")
    parser.add_argument('-i', '--interactive', required=False, action='store_true',
                        help="Interactive execution")
    parser.add_argument('-f', '--fastnet', required=False, action='store_true',
                        help="Install fastnet")
    parser.add_argument('-n', '--number', required=False, type=int,
                        help="number of time to run the test")
    parser.add_argument('-r', '--reboot', required=False, action='store_true',
                        help="Install fastnet")
    parser.add_argument('-q', '--quick_uninstall', required=False, action='store_true',
                        help="unistall without waiting the root")
    parser.add_argument('-l', '--log', required=False, action='store_true',
                        help="enable logging")
    parser.add_argument('-v', '--logcat', required=False, action='store_true',
                        help="enable logcat logging")
    parser.add_argument('-A', '--all', required=False, action='store_true',
                        help="run all devices")
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
    catchable = ['SIGINT', 'SIGQUIT', 'SIGHUP', 'SIGTERM']
    for i in catchable:
        signum = getattr(signal, i)
        signal.signal(signum, handler)
    main_cmd = ""
    for i in sys.argv[1:]:
        main_cmd += i + " "
    if args.all:
        main_cmd = ""
        for i in sys.argv[1:]:
            if i not in "-d" and i not in "-A":
                main_cmd += i + " "
        devices = get_devices_list()
        print "devices connessi: %d \n" % len(devices)

        for id in range(len(devices)):
            #print "`which python` test_install_root_unistall.py %s -d %s" % (main_cmd, devices[id])
            add_thread(myprocess.GenericThread(
                "`which python` test_install_root_uninstall.py %s -d %s" % (main_cmd, devices[id])))
    else:
        add_thread(myprocess.GenericThread("`which python` test_install_root_uninstall.py %s" % main_cmd))

    time.sleep(2)
    while something_running():
        time.sleep(2)


if __name__ == "__main__":
    main()
