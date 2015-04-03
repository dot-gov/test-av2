__author__ = 'mlosito'

import time
import threading

from AVCommon.logger import logging
from AVAgent import util_agent
import os
import socket

popup_thread = None
go_on = True
results = []
vm_global = ""
server = ""
server_error = False

learning_mode = False


def on_init(protocol, args):
    server_l = socket.gethostname()
    #parameters: 0= start/stop, 1=get files and check result, 2=learning mode
    if isinstance(args, list):
        #se l'ultimo parametro non e' l'host lo aggiunge.
        if not args[-1] == server_l:
            args.append(server_l)
        return True
    #learning mode
    else:
        logging.error("Wrong arguments. POPUP needs a **list** of 2 or 3 arguments, args = %s", args)
        return False

from AVCommon import config, tesserest_caller
from AVCommon import logger


def on_answer(vm, success, answer):

    logging.debug("POPUP answer: %s|%s" % (success, answer))

    if success:
        logging.debug("POPOP Passed, no bad images found!")

    else:
        if not isinstance(answer, list):
            logging.debug("Answer is not a list. Answer = %s", answer)

        if len(answer) == 0:
            logging.debug("Error occurred in POPOP, no bad images saved!")
        else:
            #images are already on the server!
            for result_item in answer:
                logging.debug("SAVED IMAGE: %s (%s)" % (result_item[1], result_item[0]))

            # logging.warn("We have to PULL %s images" % len(answer))
            # dir = "%s/crop" % logger.logdir
            #
            # for result_item in answer:
            #     try:
            #         src = result_item[1]
            #         dst_dir = "%s/%s" % (dir, vm)
            #         if not os.path.exists(dst_dir):
            #             os.makedirs(dst_dir)
            #
            #         src_linuxformat = src.replace('\\', '/')
            #
            #         dst = "%s/%s" % (dst_dir, os.path.basename(src_linuxformat))
            #
            #         logging.debug("PULL: %s -> %s (%s)" % (src, dst, result_item[0]))
            #         vm_manager.execute(vm, "copyFileFromGuest", src, dst)
            #     except:
            #         logging.exception("Cannot get image %s" % src)


# popup supports 2 arguments. The first is True to start monitoring and False to stop
# the second (optional) permits to disable saving of crop images (default = True, saves the files)
def execute(vm, args):
    import PIL
    global results, go_on, popup_thread, vm_global, server, learning_mode
    vm_global = vm
    output = [""]
    success = True
    startup()

    #parameters: 0= start/stop, 1=get files and check result, (optional 2=learning mode), -1 = servername
    if isinstance(args, list) and len(args) == 3:
        start, save, servername = args
    elif isinstance(args, list) and len(args) == 4:
        start, save, learning_mode, servername = args
    else:
        logging.error("Wrong arguments!!!")
        return False, "Wrong arguments!!!"

    if 'avmaster' == servername:
        server = '10.1.20.1'
    else:
        server = '10.0.20.1'

    if start:
        # starts a crop and windows server
        logging.debug("start a popup server")
        go_on = True
        try:
            #grabs firt image
            # im1 = ImageGrab.grab()
            popup_thread = threading.Thread(target=popup_loop, args=())
            popup_thread.start()
            logging.debug("Crop server exited")
            output = ["Started up popup server."]
            success = True
        except:
            output = ["EXCEPTION in POPUP detection"]
            logging.exception("problem in popup detection")
            success = False
    else:
        # stops the crop and windows server
        logging.debug("stop popup server")
        go_on = False
        if popup_thread:
            popup_thread.join()
        logging.debug("exiting, returning %s" % results)

        success = True

    if success and len(results) == 0 and not server_error:
        return True, []
    else:
        return False, results


def startup():
    if not os.path.exists(config.basedir_crop):
    #    shutil.rmtree(config.basedir_crop)
        os.makedirs(config.basedir_crop)


def popup_loop():
    global go_on, results, vm_global, server_error
    crop_num = 0
    logging.debug("grab loop")
    if not os.path.exists("crop"):
        os.mkdir("crop")

    while go_on is True:

        #makes a crop with window detection
        if learning_mode:
            util_agent.crop_window(logging, config.basedir_crop, crop_num, learning=True)
            crop_num += 1
            time.sleep(1)
            #in learning mode I do not post imagess to tesseract (too slow)
        else:
            result_c, img_files = util_agent.crop_window(logging, config.basedir_crop, crop_num)
            if result_c:
                print "POSTing images to Tesserest"
                for img_file in img_files:
                    print "POSTing: %s" % img_file
                    result_srv = tesserest_caller.post_image(img_file, host=server, av=vm_global)
                    resu, thumb_filename = tesserest_caller.parse_response(result_srv)
                    logging.info("Popup result: %s, filename: %s" % (resu, thumb_filename))
                    if not resu and "SERVER_ERROR" == thumb_filename:
                        server_error = True
                    if resu and resu not in ["NO_TEXT", "GOOD"]:
                        logging.info("This Popup needs to be reported!")
                        results.append([resu, thumb_filename])
                    crop_num += 1
                #since the call take some time I sleep less, but I sleep a little anyway not to kill the server
                time.sleep(1)
            else:
                print "Nothing detected, sleeping 2 sec."
                time.sleep(2)

    logging.debug("exiting grab_loop, found %s bad crops" % len(results))