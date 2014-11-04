__author__ = 'fabrizio'

import os
import sys
import socket
from AVCommon.logger import logging
from time import sleep
from AVCommon import config

def convert_processes(procs):
    processes = []
    if not procs:
        return None

    lines = procs.split("\n")
    if not lines:
        return None

    for l in lines[1:]:
        proc = {}
        tokens = l.split(", ", 2)
        for t in tokens:
            try:
                k,v = t.split("=", 1)
                if k == "cmd":
                    k = "name"
                proc[k] = v
            except:
                pass
        if proc:
            processes.append(proc)

    if config.verbose:
        logging.debug("processes: %s" % processes)
    return processes

def red(msg, max_len=100):
    s = str(msg)
    if len(s) < max_len:
        return s

    return "%s ..." %  s[:max_len]


def get_hostname():
    host = socket.gethostname()
    drop = ["winxp","win7","win8"]
    for d in drop:
        host = host.replace(d, "")

    return host


def get_full_hostname():
    host = socket.gethostname()

    return host