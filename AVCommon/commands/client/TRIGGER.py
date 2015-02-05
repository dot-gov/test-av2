__author__ = 'marcol'

# THERE ARE SOME CODE DUPLICATIONS. SAME CODE IS IN BUILD.PY
import ctypes
import subprocess

from AVCommon.logger import logging
from AVCommon import process


MOUSEEVENTF_MOVE = 0x0001  # mouse move
MOUSEEVENTF_ABSOLUTE = 0x8000  # absolute move
MOUSEEVENTF_MOVEABS = MOUSEEVENTF_MOVE + MOUSEEVENTF_ABSOLUTE

MOUSEEVENTF_LEFTDOWN = 0x0002  # left button down
MOUSEEVENTF_LEFTUP = 0x0004  # left button up
MOUSEEVENTF_CLICK = MOUSEEVENTF_LEFTDOWN + MOUSEEVENTF_LEFTUP


def on_init(protocol, args):
    return True


def on_answer(vm, success, answer):
    pass


def execute(vm, args):
    logging.debug("Triggering sync with mouse for 30 seconds")
    timeout = 30

    #trigger with keyinject
    subp = subprocess.Popen(['AVAgent/assets/keyinject.exe'])
    process.wait_timeout(subp, timeout)

    #trigger with python mouse clicks
    for i in range(10):
        x = 100 + i
        y = 0

        # move first
        x = 65536L * x / ctypes.windll.user32.GetSystemMetrics(0) + 1
        y = 65536L * y / ctypes.windll.user32.GetSystemMetrics(1) + 1
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVEABS, x, y, 0, 0)
        # then click
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_CLICK, 0, 0, 0, 0)

    return True, ""