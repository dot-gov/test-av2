import logging
from redis import StrictRedis
from AVCommon import config
from redis.exceptions import ConnectionError
import time

import pika

class ChannelRabbit():
    """ Communication Channel, via Redis
    A channel is defined by a (blocking) list on a redis server. Messages are strings. """

    def open(self):
        if config.verbose:
            logging.debug("    CH write, new channel %s" % self.channel_name)
        connection = pika.BlockingConnection(pika.ConnectionParameters(self.host ))
        channel = connection.channel()
        # channel.queue_declare(queue=self.channel_name)
        # Declare the queue
        channel.queue_declare(queue=self.channel_name, durable=True, exclusive=False, auto_delete=False)

        # Turn on delivery confirmations
        channel.confirm_delivery()

        return connection, channel

    def __init__(self, host, channel_name):
        """ A channel is defined by a redis host and a channel name
        """
        self.host = host
        self.channel_name = channel_name

        self.connection, self.channel = self.open()

    def clean(self):
        logging.info("DELETING: %s" % self.channel_name)
        self.channel.queue_purge(queue=self.channel_name)
        self.channel.queue_delete(queue=self.channel_name)

    def close(self):
        self.channel.close()
        self.connection.close()

    def write(self, message, from_client=None):
        assert self.channel.is_open

        """ writes a message to the channel. The channel is created automatically """
        if config.verbose:
            timestamp = time.time()
            logging.debug("    CH write: channel: %s->%s  message: %s" % (from_client,self.channel_name, message))
        ret = self.channel.basic_publish(exchange='',
                      routing_key=self.channel_name,
                      properties=pika.BasicProperties(
                            reply_to = from_client, delivery_mode = 1
                            ),
                      body=message)
        if ret:
            print 'Message publish was confirmed'
        else:
            print 'Message could not be confirmed'
        #if config.verbose:
        #    logging.debug("    CH wrote: channel: %s  delta: %s" % (self.channel_name, time.time() - timestamp))

    def read_extended(self, timeout=0):
        """ reads a message from the underlining channel. This method can be blocking or it could timeout in a while
        """
        assert self.channel.is_open
        assert self.connection.is_open

        def on_timeout():
            logging.debug("Connection TIMEOUT: %s" % timeout)
            self.connection.close()

        body = None
        if timeout:
            logging.debug("Setting TIMEOUT: %s" % timeout)
            self.connection.add_timeout(timeout, on_timeout)

        for i in range(5):
            try:
                method_frame, header_frame, body = self.channel.basic_get(self.channel_name, no_ack=True)
                break
            except Exception, ex:
                logging.info("RETRY Connect")
                self.connection, self.channel = self.open()
                time.sleep(1)

        if method_frame:
            logging.debug("    CH read: frame: %s, header: %s, body: %s" %( method_frame, header_frame, body))
            #self.channel.basic_ack(method_frame.delivery_tag)
        else:
            logging.debug("    CH no message read, channel: %s" % self.channel_name)
            return None, None

        #logging.debug("header: %s" % header_frame.reply_to)
        return header_frame.reply_to, body

    def read(self, timeout=0):
        return self.read_extended(timeout)[1]

class ChannelRedis():
    """ Communication Channel, via Redis
    A channel is defined by a (blocking) list on a redis server. Messages are strings. """
    redis = None

    def __init__(self, host, channel):
        """ A channel is defined by a redis host and a channel name
        """
        self.host = host
        self.channel = channel
        self.redis = StrictRedis(host, socket_timeout=None)
        #logging.debug("  CH init %s %s" % (host, channel))
        if not self.redis.exists(self.channel):
            if config.verbose:
                logging.debug("    CH write, new channel %s" % self.channel)

    def write(self, message):
        """ writes a message to the channel. The channel is created automatically """
        if config.verbose:
            timestamp = time.time()
            logging.debug("    CH write: channel: %s  message: %s" % (str(self.channel), str(message)))
        self.redis.rpush(self.channel, message)
        if config.verbose:
            logging.debug("    CH wrote: channel: %s  delta: %s" % (self.channel, time.time() - timestamp))

    def read(self, blocking=False, timeout=0):
        """ reads a message from the underlining channel. This method can be blocking or it could timeout in a while
        """
        ret = None
        if blocking:
            while True:
                try:
                    if config.verbose:
                        timestamp = time.time()
                        logging.debug("    CH read: channel: %s" % (str(self.channel)))
                    ret = self.redis.blpop(self.channel, timeout)
                    if config.verbose:
                        logging.debug("    CH read:  channel: %s msg: %s  delta: %s" % (self.channel, ret, time.time() - timestamp))
                    break;
                except ConnectionError, e:
                    logging.debug("    CH TIMEOUT server: %s" % e)
                    ret = None

            if not ret and timeout:
                logging.debug("    CH TIMEOUT read")
                return None

            ch, message = ret

        else:
            message = self.redis.lpop(self.channel)

        #logging.debug("  CH read: %s" % str(message))
        parsed = message

        #logging.debug("      type: %s" % type(parsed))
        return parsed

Channel=ChannelRabbit