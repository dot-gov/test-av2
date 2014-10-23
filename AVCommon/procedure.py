import sys

sys.path.append("../AVCommon")

import command
from AVCommon import config

from yaml import load

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from AVCommon.logger import logging

import pprint

pp = pprint.PrettyPrinter(indent=4)


class Procedure:
    command_list = []
    name = ""
    procedures = {}

    """docstring for Procedure"""

    def __init__(self, name, command_list=None):
        self.name = name
        if not command_list:
            self.command_list = []
        else:
            self.command_list = [command.factory(c) for c in command_list]
            assert self.command_list, "empty command_list"

    def dup(self):
        copy = Procedure(self.name)
        copy.command_list = self.command_list[:]
        return copy

    def add_begin_end(self):
        if self.command_list[0].name != "BEGIN":
            self.command_list.insert(0, command.factory("BEGIN"))
        if self.command_list[-1].name != "END":
            self.command_list.append(command.factory("END"))

    def insert_command(self, new_command):
        self.command_list.insert(0, command.factory(new_command))

    def append_command(self, new_command):
        self.command_list.append(command.factory(new_command))

    # def append_command_no_duplicates(self, new_command):
    #     if self.command_list[-1] != command.factory(new_command):
    #         self.command_list.append(command.factory(new_command))

    def insert(self, new_proc):
        self.command_list = new_proc.command_list + self.command_list

    def next_command(self):
        c = self.command_list.pop(0)
        #return command.factory(c)
        return c

    def __len__(self):
        return len(self.command_list)

    @staticmethod
    def load_from_yaml(stream, append=False):
        procedures = {}
        data = load(stream, Loader=Loader)
        #pp.pprint(data)
        for name in data.keys():
            command_list = []
            command_data = data[name]
            if config.verbose:
                logging.debug("new procedure: %s\nargs: %s" % (name, data[name]))
            for c in command_data:
                #c = command.factory(c)
                command_list.append(c)
                #logging.debug("  command: %s" % c)

            procedures[name] = Procedure(name, command_list)

        Procedure.procedures.update(procedures)
        return procedures

    @staticmethod
    def load_from_file(filename):
        stream = file(filename, 'r')
        return Procedure.load_from_yaml(stream)

    @staticmethod
    def check():
        ret = True
        called = set()
        system = []
        try:
            for name,p in Procedure.procedures.items():
                for c in p.command_list:
                    if c.name == "CALL":
                        call = c.args
                        called.add(call)
                        if call not in Procedure.procedures.keys():
                            logging.error("Error in procedure: %s, call to non existant proc: %s" % (name, call))
                            ret = False
                    if c.name == "REPORT":
                        calls = c.args
                        for c in calls:
                            call = None
                            if isinstance(c, basestring):
                                call = c
                            elif isinstance(c, dict):
                                call = c.keys()[0]
                            else:
                                logging.error("Error in procedure: %s, call to non compliant proc: %s" % (name, call))

                            if call:
                                called.add(call)
                                if call not in Procedure.procedures.keys():
                                    logging.error("Error in procedure: %s, call to non existant proc: %s" % (name, call))
                                    ret = False

            procs = set(Procedure.procedures.keys())

            for p in called:
                if p.startswith("SYSTEM_"):
                    logging.warn("system proc called: %s" % p)

            for p in procs.difference(called):
                good_start=["TEST","SYSTEM","UPDATE"]
                if not any([p.startswith(g) for g in good_start]) :
                    logging.warn("probably unused PROC: %s" % p)
                else:
                    system.append(p)

            system.sort()
            logging.info("Callable Procedures: %s" % system)
            return ret
        except:
            logging.exception("Check")

    @staticmethod
    def check_procedure(procedure):
        procedure_to_check = Procedure.procedures[procedure]
        logging.debug("\n\n  #######  Procedure to check: %s  #######  \n" % procedure_to_check.name)
        flat_command_list = []
        Procedure.print_proc(procedure_to_check, flat_command_list, limit=80)
        logging.debug("\n\n  #######  Flat command list: %s  #######  \n" % flat_command_list)
        return flat_command_list

    @staticmethod
    def print_proc(proc, flat_command_list, space="", limit=999):
        for c in proc.command_list:
            if c.name == "CALL":
                logging.debug(space + "|----, (%s)" % str(c)[:limit])
                flat_command_list.append(c.name)
                called_proc = c.args
                Procedure.print_proc(Procedure.procedures[called_proc], flat_command_list, space=space + "     ", limit=limit)
            elif c.name == "REPORT":
                logging.debug(space + "|----, (%s)" % str(c)[:limit])
                for called_proc in c.args:
                    flat_command_list.append(c.name)
                    Procedure.print_proc(Procedure.procedures[called_proc.keys()[0]], flat_command_list, space=space + "     ", limit=limit)
            else:
                logging.debug(space + "|----> %s" % str(c)[:limit])
                flat_command_list.append(c.name)