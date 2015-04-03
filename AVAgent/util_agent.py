__author__ = 'mlosito'

import socket
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

#windows os windows classnames
'''
Shell_TrayWnd (start bar)
Button (tasto windows)
ConsoleWindowClass (cmd)
Progman (desktop)
CabinetWClass (explorer) and updates
CalcFrame (calc)
Notepad
Photo_Lightweight_Viewer (window image viewer)
tooltip (popup info files)
NativeHWNDHost (win update)
NSISUACIPC (UAC)
SysShadow (UAC?)
DV2ControlHost (win start menu)
Desktop User Picture (picture on start menu)
SysDragImage (drag and drop)
#32768 (win right click menu)
TaskListOverlayWnd
TaskListThumbnailWnd
IEFrame (internet explorer)
Alternate Owner (internet explorer)
CiceroUIWndFrame (altro popup win)
'''

windows_ignore_windows = ['Shell_TrayWnd', 'Button', 'ConsoleWindowClass', 'Progman',
                   'CabinetWClass', 'CalcFrame', 'Notepad', 'Photo_Lightweight_Viewer', '#32770', 'tooltips_class32', 'NativeHWNDHost', 'NSISUACIPC',
                   'SysShadow', 'DV2ControlHost', 'Desktop User Picture', 'SysDragImage', 'NotifyIconOverflowWindow', 'ClockTooltipWindow',
                   'SysFader', '#32768', 'VANUITooltip', 'InternetExplorer_Hidden', 'TaskListOverlayWnd', 'TaskListThumbnailWnd', 'IEFrame',
                   'Alternate Owner', 'CiceroUIWndFrame']

#ok direct method WIN: Button, Cabinet,ConsoleWindowClass, progman
#not important the method for windows because we ignore these windows
# windows_printscr = ['tooltips_class32', 'Photo_Lightweight_Viewer', 'NotifyIconOverflowWindow']
#TssMainForm (skype)
#ApolloRuntimeContentWindow (air?)
#MyDialogClass (vuze)
melt_ignore_windows = ['TssMainForm', 'ApolloRuntimeContentWindow', 'MyDialogClass']

#av-specific windows classnames (homes which can be ignored)
#  securitycenter (Bitdefender home)
#ok direct method AV: securitycenter (Bitdefender home)
#AVP.SandboxWindow kis14 (check)
#MISP_TRAYUI_CLASSNAME_STR (mcafee)
#not important the method for av_ignore because we ignore these windows

av_ignore_windows = ['securitycenter', 'ESET Client Frame', 'AVP.SandboxWindow', 'MISP_TRAYUI_CLASSNAME_STR']
av_update_ignore_windows = ['QWidget', 'CisWidget']  # malwarebytes, comodo

#av-specific windows classnames which needs PRINTSCR (popups are IMPORTANT!)
av_printscr = ['bdPopupDlg', '_GDATA_SHADOW_CLASS_0000000001250000_', 'SymHTMLDialog', 'asw_av_popup_wndclass', 'WebViewHost', 'QTool'] #bitdefender, gdata, norton, avast, trendm, iobit
#av-specific windows classnames which can use DIRECT method (popups are IMPORTANT!)
av_direct = ['ESET Alert Window', '72CDF557B87B4B008B9B8402F129FF3E', 'AVP.Product_Notification', '3740880777704d7c89ABC19816EF3832', 'CisMainWizard'] #eset, adaware, kis, mcafee, comodo

#very special window class: Ghost (when application is not responding)


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


# def crop_window(logging, basedir_crop, crop_num):
#     import ImageGrab
#     filenames = []
#     try:
#         import pywinauto.findwindows as i_love_messing_whith_things
#         import pywinauto.controls.HwndWrapper as i_love_messing_whith_things_Hw
#         logging.debug("Searching popup window...")
#         #TODO: discriminate over AVS
#         # OLD: w = i_love_messing_whith_things.find_windows(class_name="bdPopupDlg")
#
#         found_windows = i_love_messing_whith_things.find_windows(top_level_only=True)
#         if found_windows is not None and found_windows != []:
#             logging.debug("Learning windows. Taking screenshots...")
#
#             for win_id in found_windows:
#                 logging.debug("Popup window found. Taking screenshots...")
#                 try:
#                     hw = i_love_messing_whith_things_Hw.HwndWrapper(win_id)
#                     win_class = hw.Class()
#                 except i_love_messing_whith_things_Hw.InvalidWindowHandle:
#                     continue
#                 #ignore the ignored windows
#                 if win_class not in windows_ignore_windows and win_class not in av_ignore_windows and win_class not in melt_ignore_windows:
#
#                 #some windows can be printed with direct method (for the others use printscr)
#                     if win_class in av_direct:
#                         #this was removed because anyway we save every 2 seconds...
#                         for imnum in range(1, 3):
#                             try:
#                                 pilimg = hw.CaptureAsImage()
#                                 print str(imnum)
#                                 time.sleep(1)
#                                 filename = "%s/%s_#%s.png" % (basedir_crop, crop_num, imnum)
#                                 filename = filename.replace('/', '\\')
#                                 filenames.append(filename)
#                                 pilimg.save(filename)
#
#                             except i_love_messing_whith_things_Hw.InvalidWindowHandle:
#                                 break
#                     else:
#                         # logging.debug("Screenshots saved.")
#                         #press printscreen
#                         ctypes.windll.user32.keybd_event(44, 0, 0, 0)
#                         time.sleep(2)
#                         pilimg = ImageGrab.grabclipboard()
#                         box = (hw.Rectangle().left,
#                                hw.Rectangle().top,
#                                hw.Rectangle().right,
#                                hw.Rectangle().bottom)
#                         cropped_pilimg = pilimg.crop(box)
#                         filename = "%s/%s_printscr.png" % (basedir_crop, crop_num)
#                         filename = filename.replace('/', '\\')
#                         filenames.append(filename)
#                         try:
#                             cropped_pilimg.save(filename)
#                         except SystemError:
#                             pilimg.save(filename.replace(".png", "_FULLcrop_error.png"))
#
#             return True, filenames
#         else:
#             return False, None
#     except ImportError:
#         import shutil as i_love_messing_whith_things
#         import os as i_love_messing_whith_things_Hw
# # if socket.gethostname() not in ["avmonitor", "rite"]:


def crop_window(logging, basedir_crop, crop_num, learning=False):
    import ImageGrab
    import re
    filenames = []
    classes = set()
    try:
        import pywinauto.findwindows as i_love_messing_whith_things
        import pywinauto.controls.HwndWrapper as i_love_messing_whith_things_Hw
        logging.debug("Searching popup window...")

        found_windows = i_love_messing_whith_things.find_windows(top_level_only=True)
        if found_windows is not None and found_windows != []:
            logging.debug("Learning windows. Taking screenshots...")
            for win_id in found_windows:
                try:
                    hw = i_love_messing_whith_things_Hw.HwndWrapper(win_id)
                    # some compatibility code because pywinauto is so nice to send me an unicode instead of the expected class, but just sometimes! Just to spice up my work!!!
                    if isinstance(hw.Class, unicode):
                        win_class = hw.Class
                    else:
                        win_class = hw.Class()
                except i_love_messing_whith_things_Hw.InvalidWindowHandle:
                        #sleep and try again!
                        time.sleep(1)
                        try:
                            hw = i_love_messing_whith_things_Hw.HwndWrapper(win_id)
                            win_class = hw.Class()
                        except i_love_messing_whith_things_Hw.InvalidWindowHandle:
                            logging.debug("###IGNORING An invalid Window (UAC?)###")
                            continue
                classes.add(win_class)
                if win_class not in windows_ignore_windows and win_class not in av_ignore_windows and win_class not in melt_ignore_windows and win_class not in av_update_ignore_windows:
                    logging.debug("Win class %s found" % win_class)

                    printable_win_class = re.sub(r'\W+', '', win_class)

                    if learning or win_class in av_direct:
                        #learning mode uses both modes: 1/2 direct
                        # non-learning uses direct only if whitelisted (printscr is bulletproof)
                        try:
                            pilimg = hw.CaptureAsImage()
                            time.sleep(1)
                            filename = "%s/%s_direct_class-%s.png" % (basedir_crop, crop_num, printable_win_class)
                            filename = filename.replace('/', '\\')
                            filenames.append(filename)
                            pilimg.save(filename)
                            logging.debug("Saved with API")
                        except (i_love_messing_whith_things_Hw.InvalidWindowHandle, AttributeError):
                            logging.debug("Impossible to save with API")

                    if learning or win_class not in av_direct:
                        #learning mode uses both modes: 2/2 printscr
                        # non-learning uses printscr by default
                        time.sleep(1)
                        ctypes.windll.user32.keybd_event(44, 0, 0, 0)
                        tries = 0
                        while hw.Rectangle().left == 0 and hw.Rectangle().top == 0 and hw.Rectangle().right == 0 and hw.Rectangle().bottom == 0:
                            logging.debug("I want to crop %s as: %s, %s, %s, %s (l, t, r, b)" % (win_class, hw.Rectangle().left, hw.Rectangle().top,
                                                                                                 hw.Rectangle().right, hw.Rectangle().bottom))

                            time.sleep(1)
                            ctypes.windll.user32.keybd_event(44, 0, 0, 0)
                            tries += 1
                            if tries > 7:
                                break
                        logging.debug("I want to crop %s as: %s, %s, %s, %s (l, t, r, b)" % (win_class, hw.Rectangle().left, hw.Rectangle().top,
                                                                                                 hw.Rectangle().right, hw.Rectangle().bottom))

                        pilimg = ImageGrab.grabclipboard()

                        box = (hw.Rectangle().left,
                               hw.Rectangle().top,
                               hw.Rectangle().right,
                               hw.Rectangle().bottom)

                        filename = "%s/%s_printscr_class-%s.png" % (basedir_crop, crop_num, printable_win_class)
                        filename = filename.replace('/', '\\')
                        filenames.append(filename)

                        try:
                            cropped_pilimg = pilimg.crop(box)
                            cropped_pilimg.save(filename)
                            logging.debug("Saved with clipboard")
                        except (SystemError, AttributeError):
                            if win_class not in classes:
                                logging.debug("Impossible to crop with clipboard, saving FULL")
                                pilimg = ImageGrab.grabclipboard()
                                pilimg.save(filename.replace(".png", "_FULLcrop_error.png"))
                            else:
                                logging.debug("Impossible to crop with clipboard, but already saved this window class, skipping")

            return True, filenames
        else:
            return False, None
    except ImportError:
        import shutil as i_love_messing_whith_things
        import os as i_love_messing_whith_things_Hw
        pywinauto.findwindows.enum_windows()