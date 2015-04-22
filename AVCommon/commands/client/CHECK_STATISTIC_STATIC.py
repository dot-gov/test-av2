import math

__author__ = 'zeno'

from AVCommon.logger import logging
import time
import glob

from AVCommon import command
from AVCommon import utils
from AVAgent import build

default_segment_size = 30
#includes three phases:
# - PUSH: [ AVAgent/assets/vira/conficker.dll, AVAgent/assets/vira/eicar.com ] OR  - PUSHZIP: [ AVAgent/assets/doc_link/* ]
# - SLEEP: 90
# - CHECK_STATIC: [ AVAgent/assets/vira/conficker.dll, AVAgent/assets/vira/eicar.com ]


# first arg is STRING OF A PATTERN TO THE DIR OF FILES. SINGLE DIR!!! LIKE ABC/DEF/*
# second size is segment size (optional, default 30)
# third argument is segment index (optional, default calculeted on year day)
def on_init(protocol, args):
    #SERVER SECTION

    logging.debug("Starting check statistic static (server side) with arguments: %s" % args)

    files_to_push = get_file_list(args)

    if files_to_push == []:
        #no files to check
        return False, "Empty files list. Check files definition."

    #if the only args is the directory, or the last argument is a number, then add the file list
    # if files_to_push and args[-1] != files_to_push:
    if len(args) == 3:
        args.append(files_to_push)
    if len(args) == 4:
        print "File list already calculated"
    if len(args) < 3:
        print "Wrong args!"
        return False

    #debug
    print "File list: files to push"
    for fil in files_to_push:
        print fil

    #zip
    success = utils.pushzip(protocol.vm, files_to_push)

    time.sleep(len(files_to_push) * 2)

    # return success
    return True


def on_answer(vm, success, answer):
    pass


def execute(vm, args):
    #VM SECTION
    logging.debug("Starting check statistic static (client side) with arguments: %s" % args)

    files_to_check = args[-1]

    logging.debug("Checking files: %s" % files_to_check)

    failed = build.check_static(files_to_check, command.context["report"])
    logging.debug("DEBUG - result from build.check_static: %s", failed)
    return failed == [], failed


def get_file_list(args):
    segment_size = segment_index = None  # this is to suppress warning

    if len(args) == 0:
        return []

    filelist = args[0]

    if len(args) == 1:
        segment_size = default_segment_size
        args.append(segment_size)
        segment_index = None
        args.append(segment_index)

    elif len(args) == 2:
        segment_size = args[1]
        segment_index = None
        args.append(segment_index)

    elif len(args) == 3:
        segment_size = args[1]
        segment_index = args[2]

    elif len(args) == 4:
        logging.debug("Selected file segment: %s" % args[3])
        return args[3]

    # logging.debug("Pushzipping files: %s" % filelist)

    files = sorted(glob.glob(filelist))

    files_to_push = get_file_portion(files, segment_size, segment_index)
    logging.debug("Selected file segment: %s" % files_to_push)

    return files_to_push


def get_file_portion(files, segment_size, segment_index):
    print "index and size: %s, %s" % (segment_index, segment_size)

    size = len(files)
    if size == 0:
        print "No files found"
        return []
    segment_number = int(math.ceil(size / segment_size))

    # segment_index = time.localtime().tm_yday % segment_size

    #uses day if not specified
    if not segment_index:
        segment_index = time.localtime().tm_yday
    #if segment index is > segment_number, uses the remainder
    selected_segment_index = segment_index % segment_number

    start = (selected_segment_index * segment_size)
    #i do not need to subtract one due to strange list slicing of python
    stop = (start + segment_size)
    if stop > size:
        stop = size

    print "start and stop: %s, %s " % (start, stop)
    print files
    print files[start:stop]
    return files[start:stop]