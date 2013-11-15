import sys

sys.path.append("../AVCommon")

import command
from AVCommon import config

from yaml import load

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import logging

import pprint

procedures = {}
pp = pprint.PrettyPrinter(indent=4)

def load_from_yaml(stream):
    global procedures
    procedures.clear()

    data = load(stream, Loader=Loader)
    pp.pprint(data)
    for name in data.keys():
        command_list = []
        command_data = data[name]
        logging.debug("new procedure: %s\nargs: %s" % (name, data[name]))
        for c in command_data:
            #c = command.factory(c)
            command_list.append(c)
            #logging.debug("  command: %s" % c)

        procedures[name] = Procedure(name, command_list)
    return procedures


def load_from_file(filename):
    stream = file(filename, 'r')
    return load_from_yaml(stream)

class Procedure:
    name = ""

    """docstring for Procedure"""

    def __init__(self, name, command_list=None):
        self.name = name
        if not command_list:
            self.command_list = []
        else:
            self.command_list = command_list
            assert self.command_list, "empty command_list"

    def add_begin_end(self):
        if self.command_list[0] != "BEGIN":
            self.command_list.insert(0, "BEGIN")
        if self.command_list[-1] != "END":
            self.command_list.append("END")

    def insert(self, new_proc):
        self.command_list = new_proc.command_list + self.command_list

    def next_command(self):
        c = self.command_list.pop(0)
        return command.factory(c)

    def __len__(self):
        return len(self.command_list)


