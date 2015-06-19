__author__ = 'mlosito'

import ctypes
from AVCommon.logger import logging


def on_init(protocol, args):
    """ server side """
    return True


def on_answer(vm, success, answer):
    """ server side """
    pass


# popup supports 2 arguments. The first is True to start monitoring and False to stop
# the second (optional) permits to disable saving of crop images (default = True, saves the files)
def execute(vm, args):
    #parameters: 0= start/stop, 1=get files and check result, (optional 2=learning mode), -1 = servername
    if not isinstance(args, list):
        logging.error("Wrong arguments!!!")
        return False, "Wrong arguments!!!"

    for c in args:
        vk = ctypes.windll.user32.VkKeyScanA(ord(c))
        scan = ctypes.windll.user32.MapVirtualKeyA(vk, 0)
        ctypes.windll.user32.keybd_event(vk, scan, 0, 0)  # char Press
        ctypes.windll.user32.keybd_event(vk, scan, 2, 0)  # char Release
        # ctypes.windll.user32.keybd_event(c, 0, 0, 0)

    return True, "Pressed: %s", str(args)
