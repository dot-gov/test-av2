__author__ = 'fabrizio'

import sys, os
sys.path.append(os.path.split(os.getcwd())[0])
sys.path.append(os.getcwd())

import logging, logging.config
from multiprocessing import Pool, Process
import threading

from AVCommon import procedure
from AVCommon.mq import MQStar
from AVMaster.dispatcher import Dispatcher
from AVMaster import vm_manager

from AVAgent import av_agent

from AVMaster.report import Report

def test_avagent_create():
    host = "localhost"

    vms = [ "testvm_%d" % i for i in range(10) ]

    test = procedure.Procedure("TEST", ["BEGIN", "START_AGENT", ("EVAL_CLIENT", None, 'vm'), "STOP_AGENT", "END"])

    host = "localhost"
    mq = MQStar(host)
    mq.clean()

    logging.debug("MQ session: %s" % mq.session)

    agent = av_agent.AVAgent("test_1", session=mq.session)
    assert agent

    #agent.start_agent()

def test_avagent_procedure():
    test = procedure.Procedure("TEST", ["BEGIN", "START_AGENT", ("EVAL_CLIENT", None, 'vm'), "STOP_AGENT", "END"])

    mq = av_agent.MQFeedProcedure(test)

    agent = av_agent.AVAgent("test_1")
    agent.start_agent(mq)


def test_avagent_get_set():
    host = "localhost"

    vms = [ "testvm_%d" % i for i in range(2) ]

    #command_client={   'COMMAND_CLIENT': [{   'SET': [   'windows'                                 'whatever']}]}

    proc = """
TEST:
    - START_AGENT
    - SET: {pippo: franco}
    - SET:
        backend: 192.168.100.201
        frontend: 172.20.100.204
        redis: 10.0.20.1
    - SET:
        android:
          binary: {admin: false, demo: true}
          melt: {}
          platform: android
          sign: {}
    - GET: pippo
    - STOP_AGENT
"""

    test = procedure.load_from_yaml(proc)

    host = "localhost"
    mq = MQStar(host)
    mq.clean()

    logging.debug("MQ session: %s" % mq.session)

    #istanzia n client e manda delle procedure.
    vm_manager.vm_conf_file = "../AVMaster/conf/vms.cfg"
    report= Report()

    # dispatcher, inoltra e riceve i comandi della procedura test sulle vm
    dispatcher = Dispatcher(mq, vms, report, timeout = 15)
    thread = threading.Thread(target=dispatcher.dispatch, args=(test["TEST"],))
    thread.start()

    agents = [ av_agent.AVAgent(v, host, mq.session,)  for v in vms]
    # i client vengono eseguiti asincronicamente e comunicano tramite redis al server

    for a in  agents:
        p = Process(target = a.start_agent)
        p.start()

    thread.join()

    logging.debug(dispatcher.report)
    logging.debug("sent: %s" % dispatcher.report.c_sent)
    logging.debug("received: %s" % Report.c_received)

if __name__ == '__main__':
    logging.config.fileConfig('../logging.conf')
    #test_avagent_create()
    test_avagent_get_set()
    #test_avagent_procedure()
