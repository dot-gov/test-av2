import sys, os
sys.path.append(os.path.split(os.getcwd())[0])
sys.path.append(os.getcwd())

from AVCommon import procedure
from AVCommon.command import Command

from AVCommon import command

import logging
import logging.config


def test_dispatcher():
    c = command.factory(["BEGIN", True, ['whatever', 'end']])
    agentFiles = ""
    params = ""

    update = procedure.Procedure("UPDATE", ["REVERT", "START_VM", "UPDATE", "STOP_VM"])
    dispatch = procedure.Procedure("DISPATCH", ["REVERT", "START_VM", ("PUSH", None, agentFiles)])
    scout = procedure.Procedure("SCOUT", [
        ("CALL", None, "dispatch"),
        ("PUSH", None, agentFiles),
    ])

    assert update
    assert dispatch
    assert scout

def test_procedure_insert():
    c = command.factory(["BEGIN", True, ['whatever', 'end']])
    agentFiles = ""
    params = ""

    p1 = procedure.Procedure("UPDATE", ["REVERT", "START_VM", "UPDATE", "STOP_VM"])
    p2 = procedure.Procedure("DISPATCH", ["REVERT", "START_VM", ("PUSH", None, agentFiles)])

    lp1= len(p1)
    lp2= len(p2)

    p1.insert(p2)

    assert p1
    assert p2
    assert len(p1) == lp1 + lp2

def test_procedure_file():
    procedures = procedure.load_from_file("../AVMaster/conf/procedures.yaml")
    assert procedures, "empty procedures"
    logging.debug("procedures: %s" % procedures)
    for p in procedures.values():
        assert isinstance(p, procedure.Procedure), "not a Procedure: %s" % p


def test_procedure_yaml():
    yaml = """UPDATE:
    - REVERT
    - START_VM
    - UPDATE
    - STOP_VM

DISPATCH:
    - REVERT
    - START_VM
    - UPDATE
    - PUSH:
        - file.sh
        - anotherfile.sh

SCOUT:
    - CALL: DISPATCH
    - START_AGENT
    - BUILD
"""
    procedures = procedure.load_from_yaml(yaml)
    assert procedures, "empty procedures"
    logging.debug("procedures: %s" % procedures)
    assert len(procedures) == 3, "wrong procedures number: %s" % len(procedures)

    for p in procedures.values():
        assert isinstance(p, procedure.Procedure), "not a Procedure: %s" % p
        assert p.name
        assert p.command_list
        assert len(p) == len(p.command_list)

    leninstance = len(procedures.values())
    lenstatic = len(procedure.procedures)
    assert leninstance == lenstatic


if __name__ == '__main__':
    logging.config.fileConfig('../logging.conf')
    test_procedure_file()
    test_procedure_yaml()
    test_dispatcher()
