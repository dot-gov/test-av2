import sys, os
sys.path.append(os.path.split(os.getcwd())[0])
sys.path.append(os.getcwd())

from AVCommon.mq import MQStar
import time
import threading
import logging
import logging.config
from redis import StrictRedis

received = []

def server(mq):
    global received
    exit = False
    logging.debug("STARTING SERVER")
    while not exit:
        c, rec = mq.receive_server(timeout=0)
        if rec is not None:
            logging.debug("%s %s" % (rec, type(rec)))
            print "SERVER RECEIVED: %s>%s" % (c, rec)
            received.append(rec)

            if rec == "STOP":
                logging.debug("EXITING")
                exit = True
        else:
            exit = True
    logging.debug("EXITING SERVER")

def test_blockingMQ():
    global received

    host = "localhost"
    mq1 = MQStar(host)
    mq2 = MQStar(host, session=mq1.session)

    c = "client1"
    mq1.add_client(c)
    thread1 = threading.Thread(target=server, args=(mq1,))
    thread1.start()

    mq2.send_server(c, "WORKS")
    mq2.send_server(c, "FINE TO THE")

    time.sleep(2)

    mq2.send_server(c, "STOP")

    time.sleep(1)
    print "RECEIVED: ", received
    assert len(received) == 3, "RECEIVED: %s" % received


def test_MultipleMQ():
    host = "localhost"
    mq1 = MQStar(host)
    mq2 = MQStar(host, session=mq1.session)

    client, message = "c1", "HELLO"
    mq1.send_server(client, message)
    c, m = mq2.receive_server()
    assert (c == client)
    assert (m == message)


def no_test_MQClean():
    return
    host = "localhost"
    mq = MQStar(host)

    redis = StrictRedis(host, socket_timeout=60)

    clients = ["c1", "c2", "c3"]
    mq.add_clients(clients)
    mq.send_client("c1", "whatever")

    rkeys = redis.keys("MQ_*")
    assert rkeys

    mq.clean()
    rkeys = redis.keys("MQ_*")
    assert not rkeys


def test_MQ():
    host = "localhost"
    mq = MQStar(host)
    mq.clean()

    clients = ["c1", "c2", "c3"]
    mq.add_clients(clients)

    for c in clients:
        mq.send_server(c, "STARTED")

    for i in range(len(clients)):
        c, m = mq.receive_server()
        assert c in clients
        assert m == "STARTED", "Uncorrect value: %s" % m
        mq.send_client(c, "END %s" % i)

    for c in clients:
        m = mq.receive_client(c)
        print m
        assert (m.startswith("END "))


if __name__ == '__main__':
    logging.config.fileConfig('../logging.conf')

    #test_MQ()
    #test_MultipleMQ()
    test_blockingMQ()

