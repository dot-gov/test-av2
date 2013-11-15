import logging
from redis import StrictRedis
from AVCommon import config
from redis.exceptions import ConnectionError
import time

class Channel():
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
