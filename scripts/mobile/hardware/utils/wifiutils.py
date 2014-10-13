from scripts.mobile.hardware.apk import apk_dataLoader

__author__ = 'mlosito'
import string
import adb

import time

#RSSM deprecated
RSSM_ssid = "RSSM"
#remember to use sigle quote in case of strange characters in password
RSSM_psk = "SteveJobsSux!_new"

TPLINK_ssid = "TP-LINK_9EF638"
#remember to use sigle quote in case of strange characters in password
TPLINK_psk = "wroadoaqle38lechlesw"

Fastnet_ssid = "Fastnet"
#remember to use sigle quote in case of strange characters in password
Fastnet_psk = "'@JG2F&38ApNnbA+'"

#starts wifi with TPLINK (internal network)
def start_wifi_av_network(dev, check_connection=True):
    start_wifi_network(TPLINK_ssid, TPLINK_psk, dev, check_connection)


#starts wifi with Fastnet (OPEN TO INTERNET!!!!)
def start_wifi_open_network(dev, check_connection=True):
    start_wifi_network(Fastnet_ssid, Fastnet_psk, dev, check_connection)


#sets NO AP on wifi config
def disable_wifi_network(dev):
    wifi_enabler = apk_dataLoader.get_apk('wifi_enabler')
    wifi_enabler.start_default_activity(dev, "-e wifi disable")

#check if connected to provided wifi network
def check_wifi_network(ssid, dev):
    wifi_enabler = apk_dataLoader.get_apk('wifi_enabler')
    wifi_enabler.start_default_activity(dev, "-e wifi info")
    log = adb.execute('logcat -d -s WifiManager', dev)
    linelist = string.split(log, '\r\n')
    lastline = linelist[-2:-1]
    #print lastline
    lastline = lastline[0]
    #print lastline
    if not ssid in lastline:
        print 'Device is connected to: %s' % ssid
        return True
    else:
        return False

#get current wifi network (unreliable)
def info_wifi_network(dev):
    wifi_enabler = apk_dataLoader.get_apk('wifi_enabler')
    wifi_enabler.start_default_activity(dev, "-e wifi info")
    log = adb.execute('logcat -d -s WifiManager', dev)
    linelist = string.split(log, '\r\n')
    lastline = linelist[-2:-1]
    #print lastline
    lastline = lastline[0]
    #print lastline
    network=lastline[string.find(lastline, ':')+2:]
    print 'Device is connected to: %s' % network
    return network


def install_wifi_enabler(dev):
    wifi_enabler = apk_dataLoader.get_apk('wifi_enabler')
    wifi_enabler.install(dev)
    return wifi_enabler

def uninstall_wifi_enabler(dev):
    wifi_enabler = apk_dataLoader.get_apk('wifi_enabler')
    wifi_enabler.uninstall(dev)
    return wifi_enabler

def start_wifi_network(ssid, psk, dev, check_connection=True):
    print "start_wifi_av_network"
    wifi_enabler = apk_dataLoader.get_apk('wifi_enabler')
    wifi_enabler.start_default_activity(dev, "--es SSID " + ssid + " --es psk " + psk)
    #ensures you are connected to the desired network
    if check_connection:
        while ssid != info_wifi_network(dev):
            time.sleep(1)
    #other method
    # while not check_wifi_network(ssid,dev):
    #      time.sleep(1)


def ping_google(dev):
    result = adb.execute_no_command_split("/system/bin/ping -n -c 2 -w 3 173.194.35.114 > /dev/null; echo $?", dev)
    return result
