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
vm_error = False

learning_mode = False


def on_init(protocol, args):
    server_l = socket.gethostname()
    #parameters: 0= start/stop, 1=get files and check result, 2=learning mode
    if isinstance(args, list):
        #se l'ultimo parametro non e' l'host lo aggiunge.
        if not args[-1] == server_l:
            args.append(server_l)
        return True
    else:
        logging.error("Wrong arguments. POPUP needs a **list** of 2 or 3 arguments, args = %s", args)
        return False

from AVCommon import config, tesserest_caller
from AVCommon import logger


def on_answer(vm, success, answer):

    logging.debug("POPUP answer: %s|%s" % (success, answer))

    if success:
        if not isinstance(answer, list):
            logging.debug("POPUP Success. Answer: %s", answer)

    else:
        if not isinstance(answer, list):
            logging.debug("POPUP Failed. Answer: %s", answer)

        if len(answer) == 0:
            logging.debug("Error occurred in POPUP, no bad images saved!")
        else:
            #images are already on the server!
            for result_item in answer:
                logging.debug("SAVED IMAGE: %s (%s, word: %s)" % (result_item[1], result_item[0], result_item[2]))



# popup supports 2 arguments. The first is True to start monitoring and False to stop
# the second (optional) permits to disable saving of crop images (default = True, saves the files)
def execute(vm, args):
    global results, go_on, popup_thread, vm_global, server, learning_mode, vm_error
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
            output = ["EXCEPTION in POPUP startup"]
            logging.exception("problem in popup detection")
            success = False
        # return on start popup
        return success, output
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
        if vm_error:
            return False, "ERROR on VM. Probably libraries are not installed. Impossible to screenshot."
        else:
            return False, results


def startup():
    if not os.path.exists(config.basedir_crop):
    #    shutil.rmtree(config.basedir_crop)
        os.makedirs(config.basedir_crop)


def popup_loop():
    global go_on, results, vm_global, server_error, vm_error
    logging.debug("grab loop")
    if not os.path.exists("crop"):
        os.mkdir("crop")

    image_hashes = []

    while go_on is True:
        timestamp = time.strftime("%y%m%d-%H%M%S", time.localtime(time.time()))
        #makes a crop with window detection
        if learning_mode:
            util_agent.crop_window(logging, config.basedir_crop, timestamp, learning=True, image_hashes=None)
            time.sleep(1)
            #in learning mode I do not post imagess to tesseract (too slow)
        else:
            result_c, img_files = util_agent.crop_window(logging, config.basedir_crop, timestamp, image_hashes=image_hashes)
            if result_c:
                # print "POSTing images to Tesserest"
                for img_file in img_files:
                    if not os.path.exists(img_file):
                        print "BIG ERROR! File: %s does not exists! Not posting to tesserest!" % img_file
                        continue
                    print "POSTing: %s to Tesserest" % img_file
                    result_srv = tesserest_caller.post_image(img_file, host=server, av=vm_global)
                    resu, thumb_filename, word = tesserest_caller.parse_response(result_srv, server)
                    logging.info("Popup result: %s, filename: %s, found word: %s" % (resu, thumb_filename, word))
                    if not resu and "SERVER_ERROR" == thumb_filename:
                        server_error = True
                    if resu and resu not in ["NO_TEXT", "GOOD"]:
                        logging.info("This Popup needs to be reported!")
                        results.append([resu, thumb_filename, word])
                #since the call take some time I sleep less, but I sleep a little anyway not to kill the server
                time.sleep(1)
            else:
                if img_files is None:
                    print "Nothing detected, sleeping 2 sec."
                    time.sleep(2)
                else:
                    #SERIOUS ERROR OCCURRED
                    print "ERROR! Cannot use POPUP. Try to reinstall LIBS!"
                    vm_error = True
                    time.sleep(2)

    logging.debug("exiting grab_loop, found %s bad crops" % len(results))