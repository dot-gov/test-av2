__author__ = 'fabrizio'

import logging as l
#import logging.config
import yaml
import os
import time

from AVCommon import package

logname = "avmonitor.log"
logdir_base = "%s/logs" % ( package.basedir )
logdir = logdir_base

if not os.path.exists(logdir):
    os.mkdir(logdir)

#with open("../AVCommon/logging.yml") as o:
#    logging.config.dictConfig(yaml.load(o))

class LogWrap:
    def __getattr__(self, item):
        logger = l.getLogger('AVM')
        return logger.__getattribute__(item)

logging = LogWrap()


def init(report = "", logname_arg = "avmonitor.log", quiet=False):
    #print "init report: %s" % report
    global logdir, logname

    if report:
        logdir = "%s/%s" % (logdir_base, report)
        if not os.path.exists(logdir):
            os.mkdir(logdir)
        logname = logname_arg
        if not quiet:
            setStreamLogger()
        logging = setFileLogger(logdir, logname_arg)

    else:
        logging = setStreamLogger()

    #globals()["logging"] = logging

def setStreamLogger():
    # TODO
    ts = time.strftime("%y%m%d-%H%M%S", time.localtime(time.time()))

    FORMAT= '%(asctime)s %(levelname)7s %(filename)14s:%(lineno)3d| %(message)s'
    DATE_FORMAT= '%Y%m%d %H%M%S'

    formatter = l.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)

    handler = l.StreamHandler()
    handler.setFormatter(formatter)

    logger = l.getLogger('AVM')
    logger.setLevel(l.DEBUG)
    logger.addHandler(handler)

    return logger

def setFileLogger(report_dir, logname_arg):
    ts = time.strftime("%y%m%d-%H%M%S", time.localtime(time.time()))

    FORMAT= '%(asctime)s %(levelname)7s %(filename)14s:%(lineno)3d| %(message)s'
    DATE_FORMAT= '%Y%m%d %H%M%S'

    formatter = l.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
    #filename = "%s/avmonitor-%s.log" % (logdir, ts)

    if not os.path.exists(report_dir):
        os.mkdir(report_dir)

    #filename  = "%s/avmonitor-%s.log" % (report_dir, ts)
    filename  = "%s/%s" % (report_dir, logname_arg)
    file_handler = l.FileHandler(filename)
    file_handler.setLevel(l.DEBUG)
    file_handler.setFormatter(formatter)

    #handler = l.StreamHandler()
    #handler.setFormatter(formatter)

    logger = l.getLogger('AVM')
    logger.setLevel(l.DEBUG)

    #logger.addHandler(handler)
    logger.addHandler(file_handler)

    logger.info("START %s" % (report_dir))

    return logger

#init()
#logging.info("START LOGGING")