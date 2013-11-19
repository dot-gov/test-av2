import string
import random
import logging
import time

from channel import Channel
from AVCommon import config

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


class MQStar():
    """ MQStar is a Message Queue with a star topology. There's a server and multiple clients.
    Each mqstar is identified by a session, which is the name of the underlining redis channels.
    A server can send messages to clients on different channels, but receives answers on one channel: channel_to_server

    """
    session = ""
    channels = {}
    """MQStar is a MessageQueue with a star topology based on Redis"""

    def make_channel_server(self):
        channel_server = "MQ_%s_to_server" % self.session
        self.channel_to_server = Channel(self.host, channel_server)

    def __init__(self, host, session=None):
        self.host = host
        if not session:
            self.session = id_generator()
        else:
            self.session = session

        #time.sleep(1)
        self.make_channel_server()

    def _make_channel(self, frm="server", to="server"):
        name = "MQ_%s_%s_%s" % (self.session, frm, to)
        channel = Channel(self.host, name)
        return channel

    def clean(self, av=None):
        """ Cleans all the redis keys related to the used channels
        """
        if av:
            key = "MQ_*_server_%s" % av
        else:
            key = "MQ_*"

        #for k in self.channel_to_server.redis.keys(key):
        #    logging.debug(" MQ clean %s" % k)
        #    self.channel_to_server.redis.delete(k)

        self.channel_to_server.clean()
        self.make_channel_server()

        #assert not self.channel_to_server.redis.keys("MQ_*")

    def add_client(self, client):
        if client not in self.channels.keys():
            ch = self._make_channel(to=client)
            #chRight = self.channelToServer
            self.channels[client] = ch

    def add_clients(self, clients):
        for c in clients:
            self.add_client(c)

    def send_server(self, client, message):
        if client not in self.channels.keys():
            logging.debug(" MQ error, client not found")
        ch = self.channel_to_server
        payload = message
        ch.write(payload, from_client=client)

    def receive_server(self, timeout=0):
        #logging.debug(" MQ receive_server")
        client, payload = self.channel_to_server.read_extended(timeout)

        if not payload:
            logging.error("TIMEOUT: %s,%s" %(client, payload))
            return None, None

        return client, payload

    def send_client(self,  client, message):
        if client not in self.channels.keys():
            logging.debug(" MQ error, sendClient, client not found: %s" %
                self.channels)
        ch = self.channels[client]
        ch.write(message)

    def receive_client(self, client, timeout=0):
        assert(isinstance(client, str))
        if client not in self.channels.keys():
            logging.debug(" MQ error, receiveClient, client (%s) not found: %s" % (client, self.channels))
        ch = self.channels[client]
        message = ch.read(timeout)
        if not message:
            logging.error("TIMEOUT")
        return message

