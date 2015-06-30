import random
import traceback

__author__ = 'mlosito'

import ctypes
import subprocess
import time
import md5

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
EdgeUiInputTopWndClass (windows 8)
TfrmStartMenu (tasto windows 8.1)
BaseBar (menu win 32)
MUSHYBAR (xps viewer o other win window)
Windows.UI.Core.CoreWindow (windows 10 interface)
ApplicationFrameWindow (windows 10 interface)
TaskManagerWindow (task manager)

'''

windows_ignore_windows = ['Shell_TrayWnd', 'Button', 'ConsoleWindowClass', 'Progman',
                   'CabinetWClass', 'CalcFrame', 'Notepad', 'Photo_Lightweight_Viewer', '#32770', 'tooltips_class32', 'NativeHWNDHost', 'NSISUACIPC',
                   'SysShadow', 'DV2ControlHost', 'Desktop User Picture', 'SysDragImage', 'NotifyIconOverflowWindow', 'ClockTooltipWindow',
                   'SysFader', '#32768', 'VANUITooltip', 'Internet Explorer_Hidden', 'Internet_Explorer_Hidden', 'TaskListOverlayWnd',
                   'TaskListThumbnailWnd', 'IEFrame',
                   'Alternate Owner', 'CiceroUIWndFrame', 'Explorer_Hidden', 'EdgeUiInputTopWndClass', 'TfrmStartMenu', 'BaseBar', 'MUSHYBAR',
                   'Windows.UI.Core.CoreWindow', 'ApplicationFrameWindow', 'TaskManagerWindow']

#ok direct method WIN: Button, Cabinet,ConsoleWindowClass, progman
#not important the method for windows because we ignore these windows
# windows_printscr = ['tooltips_class32', 'Photo_Lightweight_Viewer', 'NotifyIconOverflowWindow']
#TssMainForm (skype)
#ApolloRuntimeContentWindow (air?) AIR OK
#MyDialogClass (vuze)
#utorrent OK
melt_ignore_windows = ['TssMainForm', 'ApolloRuntimeContentWindow', 'MyDialogClass']

#av-specific windows classnames (homes which can be ignored)
#  securitycenter (Bitdefender home)
#ok direct method AV: securitycenter (Bitdefender home)
#AVP.SandboxWindow kis14 (check)
#MISP_TRAYUI_CLASSNAME_STR (mcafee)
#TPSUAConsoleForm (Panda15)
#SideBar_HTMLHostWindow (avast)
#BasicWindow (avast)
#WebViewHost (trendm15)
#not important the method for av_ignore because we ignore these windows

av_ignore_windows = ['securitycenter', 'ESET Client Frame', 'AVP.SandboxWindow', 'MISP_TRAYUI_CLASSNAME_STR', 'TPSUAConsoleForm', 'SideBar_HTMLHostWindow', 'BasicWindow', 'WebViewHost', 'Afx00000000004000003000000000001000300000000019000100000000000010027']
av_update_ignore_windows = ['QWidget', 'CisWidget']  # malwarebytes, comodo

av_scan_ignore_windows = ['Sym_Common_Scan_Window', 'TAnalisisWindow', 'TfrmAvisoConexion']  # norton, panda, panda

#av-specific windows classnames which needs PRINTSCR (popups are IMPORTANT!)
av_printscr = ['bdPopupDlg', '_GDATA_SHADOW_CLASS_0000000001250000_', 'SymHTMLDialog', 'asw_av_popup_wndclass', 'WebViewHost', 'QTool'] #bitdefender, gdata, norton, avast, trendm, iobit
#av-specific windows classnames which can use DIRECT method (popups are IMPORTANT!)
av_direct = ['72CDF557B87B4B008B9B8402F129FF3E', 'AVP.Product_Notification', '3740880777704d7c89ABC19816EF3832', 'CisMainWizard', 'ESET Layer Window', 'ESET Desktop Window'] # adaware, kis, mcafee, comodo
#rimosso: 'ESET Alert Window' (eset)
# '' HwndWrapperDefaultDomainWpf76134ef4002e440389298af68adebca9
#QTool (norman)

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


def get_box_for_cropping(logging, win_id, hw, wrapper):
    tries = 0
    while not hw.Rectangle() or (hw.Rectangle().left == 0 and hw.Rectangle().top == 0 and hw.Rectangle().right == 0 and hw.Rectangle().bottom == 0):
        logging.debug("Cropping would be 0,0,0,0, I try again)")
        ctypes.windll.user32.keybd_event(44, 0, 0, 0)
        time.sleep(1)
        hw = wrapper.HwndWrapper(win_id)
        tries += 1
        if tries > 4:
            return False, hw
    # return anyway the latest hw
    return True, hw


def crop_window(logging, basedir_crop, timestamp, learning=False, image_hashes=None):
    import ImageGrab
    import re
    filenames = []
    classes = set()
    try:
        #this is necessary because pywinauto cannot be installed on Linux
        #we try to late import, and fail badly if cannot find the import.
        import pywinauto.findwindows as findwind
        import pywinauto.controls.HwndWrapper as Wrapper
        logging.debug("Searching popup window...")

        found_windows = findwind.find_windows(top_level_only=True)
        if found_windows is not None and found_windows != []:
            # logging.debug("Learning windows. Taking screenshots...")
            for win_id in found_windows:
                hw, win_class = win_id_to_class(win_id, Wrapper)
                if not win_class:
                    logging.debug("###IGNORING An invalid Window (UAC?)###")
                    continue

                classes.add(win_class)

                if learning:
                    logging.debug("Learning, printing all classes: Win class %s " % win_class)

                if win_class not in windows_ignore_windows and win_class not in av_ignore_windows and win_class not in melt_ignore_windows and \
                        win_class not in av_update_ignore_windows and win_class not in av_scan_ignore_windows:
                    logging.debug("Win class %s" % win_class)

                    printable_win_class = re.sub(r'\W+', '', win_class)

                    #learning mode uses both modes: 1/2 direct
                    # non-learning uses direct only if whitelisted (printscr is bulletproof)
                    if learning or win_class in av_direct:
                        try:
                            pilimg = hw.CaptureAsImage()
                            time.sleep(1)
                            filename = "%s/%s_direct_class-%s.png" % (basedir_crop, timestamp, printable_win_class)
                            filename = filename.replace('/', '\\')
                            # filenames.append(filename)
                            # pilimg.save(filename)
                            if save_if_new(pilimg, filename, filenames, image_hashes):
                                logging.debug("Saved with API")
                        except (Wrapper.InvalidWindowHandle, AttributeError):
                            logging.debug("Impossible to save with API")

                    #learning mode uses both modes: 2/2 printscr
                    # non-learning uses printscr by default
                    if learning or win_class not in av_direct:
                        time.sleep(1)

                        ctypes.windll.user32.keybd_event(44, 0, 0, 0)
                        filename = "%s/%s_printscr_class-%s.png" % (basedir_crop, timestamp, printable_win_class)
                        filename = filename.replace('/', '\\')
                        # filenames.append(filename)

                        try:
                            #until the rectangle is 0,0,0,0 i re-grab the screen
                            got_valid_box, hw = get_box_for_cropping(logging, win_id, hw, Wrapper)

                            logging.debug("I want to crop %s as: %s, %s, %s, %s (l, t, r, b)" % (win_class, hw.Rectangle().left, hw.Rectangle().top,
                                                                                                 hw.Rectangle().right, hw.Rectangle().bottom))

                            pilimg = None
                            i = 0
                            #until the image is null, I re-capture from clipboard (max 8 times or it blocks other windows)
                            while pilimg is None and i < 8:
                                try:
                                    pilimg = ImageGrab.grabclipboard()
                                except NameError:
                                    return False, "ERROR: Image Library Missing!"
                                time.sleep(1)
                                print "Checking if image is in clipboard"
                                i += 1

                            #if the box is valid
                            if hw.Rectangle().left != 0 or hw.Rectangle().top != 0 or hw.Rectangle().right != 0 or hw.Rectangle().bottom != 0:
                                box = (hw.Rectangle().left,
                                       hw.Rectangle().top,
                                       hw.Rectangle().right,
                                       hw.Rectangle().bottom)
                                cropped_pilimg = pilimg.crop(box)
                                #cropped_pilimg.save(filename)
                                if save_if_new(cropped_pilimg, filename, filenames, image_hashes):
                                    logging.debug("Saved with clipboard")
                            else:
                                if got_valid_box or win_class == 'InternetExplorer_Hidden':
                                    logging.debug("Skipping because probably the windows was closed or class is InternetExplorer_Hidden.")
                                else:
                                    if save_if_new(pilimg, filename + "_FULL_invalid_box.png", filenames, image_hashes):
                                        logging.debug("Saved with clipboard but no crop (invalid box)")

                        except Wrapper.InvalidWindowHandle:
                            logging.debug("Skipping because probably the windows %s was closed." % win_class)
                        except(SystemError, AttributeError, TypeError):
                            logging.debug("Here I print the stacktrace but we have fallback methods so don't worry.")
                            traceback.print_exc()
                            try:
                                ctypes.windll.user32.keybd_event(44, 0, 0, 0)
                                time.sleep(1)
                                logging.debug("Exception, trying again to save FULL")
                                pilimg = ImageGrab.grabclipboard()
                                time.sleep(1)
                                #pilimg.save(filename.replace(".png", "_FULLcrop_error%s.png" % random.randint(0, 99999)))
                                if save_if_new(pilimg, filename.replace(".png", "_FULL_exception%s.png" % random.randint(0, 99999)), filenames, image_hashes):
                                    logging.debug("Saved with clipboard FULL")

                            except:
                                traceback.print_exc()
                                logging.debug("Impossible to save FULL (cannot screenshot at all)")

            return True, filenames
        else:
            return False, None
    except ImportError:
        import shutil as findwind
        import os as Wrapper
        # pywinauto.findwindows.enum_windows()
        return False, "ERROR: Import error!"


def win_id_to_class(win_id, wrapper):
    #tries 3 times
    for i in range(3):
        try:
            hw = wrapper.HwndWrapper(win_id)
            # some compatibility code because pywinauto is so nice to send me an unicode instead of the expected class, but just sometimes! Just to spice up my work!!!
            if isinstance(hw.Class, unicode):
                return hw, hw.Class
            else:
                return hw, hw.Class()
        except wrapper.InvalidWindowHandle:
            #sleep and try again!
            time.sleep(1)
    return None, None


def save_if_new(image, filename, filenames, image_hashes):
    w, h = image.size
    if w == 0 and h == 0:
        print "Skipping 0*0 image"
        return False
    img_hash = md5.new(image.tostring()).hexdigest()
    if image_hashes is None or img_hash not in image_hashes:
        image.save(filename)
        print "Saved new image with hash %s" % img_hash
        if image_hashes is not None:
            image_hashes.append(img_hash)
        filenames.append(filename)
        return True
    else:
        print "Image with hash %s skipped" % img_hash
        return False
