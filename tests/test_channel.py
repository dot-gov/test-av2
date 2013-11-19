from unittest import TestCase
import os
import sys
sys.path.append(os.path.split(os.getcwd())[0])
sys.path.append(os.getcwd())

import time
import thread
from redis import StrictRedis
import ast
import string
import random
import logging, sys
import logging.config
from functools import partial
import unittest

from AVCommon.channel import Channel

__author__ = 'zeno'

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

def binary_generator(size=6, chars=range(256)):
    return ''.join(chr(random.choice(chars)) for x in range(size))

def server(s):
    global count
    for c, m in s.read():
        print "RECEIVED: %s | %s" % (c, m)
        count += 1

#
class TestChannel(unittest.TestCase):

    def no_test_Redis(self):
        host = "localhost"
        r = StrictRedis(host, socket_timeout=60)
        msg = "Hello world"

        r.delete("channel")
        r.rpush("channel", msg)
        m = r.lpop("channel")
        print m
        assert(m == msg)

        r.rpush("channel", [1, 2, 3])
        m = ast.literal_eval(r.lpop("channel"))
        print m, type(m)

    def test_ChannelTimeout(self):
        logging.debug("test_ChannelTimeout")
        channel = "test"
        host = "localhost"
        s = Channel(host, channel)
        r = s.read(timeout=1)
        assert r is None

        #s.close()

    def test_ChannelList(self):
        logging.debug("test_ChannelList")
        global count
        channel = "response"
        host = "localhost"

        s = Channel(host, channel)
        c1 = Channel(host, channel + ".c1")
        c2 = Channel(host, channel + ".c2")

        logging.debug("writing clients")
        c1.write("START")
        c2.write("START")

        logging.debug("reading clients")
        rc1 = c1.read()
        rc2 = c2.read()

        logging.debug("writing server")
        s.write("+STARTED C1")
        s.write("+STARTED C2")

        logging.debug("reading server")
        r3 = s.read()
        r4 = s.read()

        assert rc1 == "START", "not a START: %s" % rc1
        assert(rc2 == "START")
        assert(r3 == "+STARTED C1")
        assert(r4 == "+STARTED C2")

        #s.close()
        #c1.close()
        #c2.close()

    def test_ChannelRandom(self):
        logging.debug("test_ChannelRandom")
        global count
        channel = id_generator()
        host = "localhost"

        c1 = Channel(host, channel + ".c1")
        #c1.clean()

        messages = [ id_generator(size=1000) for i in range(10)]

        for m in messages:
            c1.write(m, "whatever")
        #c1.close()

        c1 = Channel(host, channel + ".c1")

        for m in messages:
            r = c1.read()
            assert m == r, "not equal: %s" % r
        #c1.close()

    def test_ChannelCallback(self):
        logging.debug("test_ChannelCallback")
        global count
        channel = id_generator()
        host = "localhost"

        c1 = Channel(host, channel + ".c1")
        #c1.clean()

        messages = [ id_generator(size=10) for i in range(10)]

        for m in messages:
            c1.write(m, "whatever")
        c1.close()

        c1 = Channel(host, channel + ".c1")

        n = 0
        def callback(ch, body):
            assert body
            assert body in messages, "not in messages: %s" % (body)
            logging.debug("read: %s" % body)
            n+=1
            if n >= len(messages):
                logging.debug("closing channel")
                c1.channel.close()

        for m in messages:
            c1.read_callback(callback)

        c1.channel.start_consuming()
        logging.debug("finished consuming")
        #c1.close()

    def no_test_ChannelBinary(self):
        global count
        channel = id_generator()
        host = "localhost"

        c1 = Channel(host, channel + ".c1")
        c1.clean()

        messages = [ binary_generator(size=100) for i in range(10)]

        n = 0
        logging.debug("sending %s messages" % len(messages))
        for m in messages:
            c1.write(m, "server")
            n+=1

        #c1.close()

        logging.debug("sent %s messages" % n)
        logging.debug("channel dir: %s" % dir(c1.channel))

        n=0
        for m in messages:
            r = c1.read()
            n+=1
            logging.debug("received %s message: %s" % (n, r))

            assert m == r, "got: %s" % r

if __name__ == '__main__':
    logging.config.fileConfig('../logging.conf')

    #test_dispatcher_server()
    unittest.main()
    #TestChannel.test_ChannelBinary()