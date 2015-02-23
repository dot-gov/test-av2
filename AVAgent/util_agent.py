__author__ = 'mlosito'

import ctypes
import subprocess
import time


from AVCommon import process

MOUSEEVENTF_MOVE = 0x0001  # mouse move
MOUSEEVENTF_ABSOLUTE = 0x8000  # absolute move
MOUSEEVENTF_MOVEABS = MOUSEEVENTF_MOVE + MOUSEEVENTF_ABSOLUTE

MOUSEEVENTF_LEFTDOWN = 0x0002  # left button down
MOUSEEVENTF_LEFTUP = 0x0004  # left button up
MOUSEEVENTF_CLICK = MOUSEEVENTF_LEFTDOWN + MOUSEEVENTF_LEFTUP


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_uint),
        ('dwTime', ctypes.c_uint),
    ]


def get_idle_duration():
    lastinputinfo = LASTINPUTINFO()
    lastinputinfo.cbSize = ctypes.sizeof(lastinputinfo)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastinputinfo))
    millis = ctypes.windll.kernel32.GetTickCount() - lastinputinfo.dwTime
    return millis / 1000.0


def trigger_worked(logging):
    idle_time_after_trigger = get_idle_duration()
    logging.debug("Idle time AFTER trigger: %s", idle_time_after_trigger)
    if idle_time_after_trigger > 20.0:
        logging.debug("TRIGGER FAILED!!! Idle time after trigger: %s" % idle_time_after_trigger)
        return False, "TRIGGER FAILED!!! Idle time after trigger: %s" % idle_time_after_trigger
    else:
        logging.debug("TRIGGER SUCCESS. Idle time after trigger: %s" % idle_time_after_trigger)
        return True, "TRIGGER Worked. Idle time after trigger: %s" % idle_time_after_trigger


def trigger_keyinject(timeout=30):
    # trigger with keyinject
    subp = subprocess.Popen(['AVAgent/assets/keyinject.exe'])
    process.wait_timeout(subp, timeout)


def trigger_python_mouse():
    # trigger with python mouse clicks
    for i in range(10):
        x = 100 + i
        y = 0
        time.sleep(1)
        # move first
        x = 65536L * x / ctypes.windll.user32.GetSystemMetrics(0) + 1
        y = 65536L * y / ctypes.windll.user32.GetSystemMetrics(1) + 1
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVEABS, x, y, 0, 0)
        # then click
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_CLICK, 0, 0, 0, 0)