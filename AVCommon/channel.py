import logging
from AVCommon import config
import time

import pika
from functools import partial
from threading import Condition

class Channel():
    """ Communication Channel, via Redis
    A channel is defined by a (blocking) list on a redis server. Messages are strings. """

    def open(self):
        if config.verbose:
            logging.debug("    CH write, new channel %s" % self.channel_name)
        connection = pika.BlockingConnection(pika.ConnectionParameters(self.host ))
        channel = connection.channel()
        # channel.queue_declare(queue=self.channel_name)
        # Declare the queue
        channel.queue_declare(queue=self.channel_name)
        channel.basic_qos(prefetch_count=1)

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
        #self.channel.queue_delete(queue=self.channel_name)

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
                            reply_to = from_client
                            ),
                      body=message)
        if ret:
            if config.verbose:
                logging.debug('Message publish was confirmed')
        else:
            logging.debug('Message could not be confirmed')



    def read_callback(self, callback):
        """ reads a message from the underlining channel. This method can be blocking or it could timeout in a while
        """
        assert self.channel.is_open
        assert self.connection.is_open

        def _callback( ch, method, properties, body, callback=None):
            logging.debug("called_callback, ch: %s body: %s, cb: %s" % (ch, body, callback))
            #if method:
            #    ch.basic_ack(method.delivery_tag)
            callback(properties.from_client, body)

        cb = partial(_callback, callback=callback)

        self.channel.basic_consume(cb, queue=self.channel_name, no_ack=True)

    def read_extended(self, timeout=None):
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

        timestamp = time.time();
        method_frame = None
        while not method_frame:
            method_frame, header_frame, body = self.channel.basic_get(queue=self.channel_name, no_ack=False)
            if timeout and (time.time() - timestamp) < timeout:
                break
            time.sleep(0.1)

        if method_frame:
            logging.debug("got answer")
            self.channel.basic_ack(delivery_tag = method_frame.delivery_tag)
        else:
            logging.debug("got nothing")
            return None, None

        return header_frame.reply_to, body

    def read(self, timeout=None):
        av, msg = self.read_extended(timeout)
        logging.debug("READ: %s, %s" %(av, msg))
        return msg

