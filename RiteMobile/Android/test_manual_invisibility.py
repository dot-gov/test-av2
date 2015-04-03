import sys
import csv
import traceback
import time
import os

# our files
from RiteMobile.Android import adb
from RiteMobile.Android.commands_device import CommandsDevice
from RiteMobile.Android.apk import apk_dataLoader
from RiteMobile.Android.utils import utils
from RiteMobile.Android.utils import wifiutils


def get_which_av():
    print 'Choose one av:'
    print str(apk_dataLoader.get_av_list())
    av = raw_input()
    return av


def main(argv):

    print """
    !!! Test AntiVirus !!!
    !!! Attenzione:    !!!
    !!! Prima dell'installazione dell'agente, al dispositivo va impedito il libero accesso ad internet. !!!
    """
    print """ prerequisiti:
    1) Telefono connesso in USB,
    2) USB Debugging enabled (settings/developer options/usb debugging)
    3) NESSUNA SIM INSTALLATA <======== NB!!!!!!!!!!!!!!!!!!!!!!!
    4) screen time 2m (settings/display/sleep)
    """

    comm_dev = CommandsDevice()

    #some debug
    # print comm_dev.get_adb_client()
    # print comm_dev.get_adb_client().serialno
    # print comm_dev.get_dev_serialno()

    init = raw_input('Init everything? (y/n)')
    if init == "y":
        print "Init!"
        comm_dev.init_device(install_eicar=True)

    operation = -1

    while operation not in ["99", "69"]:
        print ''
        print '#################       OPERATIONS      #################'
        print 'What operation do you want to perform?'
        print '1  - get new configuration from installed av'
        print '2  - use net Fastnet'
        print '2a  - use net Fastnet - no network check'
        print '3  - use net TPLINK'
        print '3a  - use net TPLINK - no network check'
        print '4  - disable net'
        print '5  - get wifi network name'
        print '6  - ping google'
        print '7  - test all avs'
        print '8  - test a single av'
        print '8a  - test a single av (no update)'
        print '9 - is infected?'
        print '10 - got r00t?'
        print '11 - pull file'
        print '12 - push file'
        print ''
        print '#################     INTERNAL TESTS    #################'
        print '20 - DEPRECATED test get_server'
        print '21 - DEPRECATED test set_server'
        print '22 - test get_client'
        print '23 - test set_client'
        print '24 - test install (test on wifi_enabler)'
        print '25 - test install_agent'
        print '26 - test uninstall (test on wifi_enabler)'
        print '27 - test uninstall_agent'
        print '28 - test execute (test on wifi_enabler)'
        print '29 - test execute_agent'
        print '30 - DEPRECATED test build_agent'
        print '31 - DEPRECATED test build_agent (overwrite)'
        print '32 - test backup app data'
        print '33 - test restore app data from backup'
        print '34 - test restore app data from one of the sources'
        print '35 - test get new apk for an av'
        print ''
        print '#################          EXIT         #################'
        print '69 - Exit (no cleanup)!'
        print '99 - Clean & exit!'

        operation = raw_input()

        if operation == '1':
            av = get_which_av()
            comm_dev.update(av)

        elif operation == '2':
            comm_dev.wifi('open')

        #no network check
        elif operation == '2a':
            comm_dev.wifi('open', False)

        elif operation == '3':
            comm_dev.wifi('av')

        #no network check
        elif operation == '3a':
            comm_dev.wifi('av', False)

        elif operation == '4':
            comm_dev.wifi('disable')

        elif operation == '5':
            print comm_dev.info_wifi_network()

        elif operation == '6':
            if comm_dev.can_ping_google():
                print "I can ping google"
            else:
                print "I canNOT ping google"

        elif operation == '7':
            # TODO: andrebbe spostato il do_test
            for av in apk_dataLoader.get_av_list():
                do_test(comm_dev.get_dev_deviceid(), av)

        elif operation == '8':
            # TODO: andrebbe spostato il do_test
            av = get_which_av()
            do_test(comm_dev.get_dev_deviceid(), av)

        elif operation == '8a':
            # TODO: andrebbe spostato il do_test
            av = get_which_av()
            do_test(comm_dev.get_dev_deviceid(), av, av_update=False)

        elif operation == '9':
            if comm_dev.check_infection():
                print "Infected"
            else:
                print "Clean"

        elif operation == '10':
            if comm_dev.check_su_permissions():
                print "Root!"
            else:
                print "Not root :("
        elif operation == '11':
            print '12 - pull file'
            comm_dev.pull(['file.png'], '/sdcard/', 'tmp')
            if os.path.exists('tmp/file.png'):
                print 'Pull OK!'
                #debug: time.sleep(20)
                os.remove('tmp/file.png')
            else:
                print 'Pull failed!'

        elif operation == '12':
            print '13 - push file'
            comm_dev.push(['file.png'], 'assets', '/sdcard/')
        #DEPRECATED
        # elif operation == '20':
        #     print "testvarsrv= " + comm_dev.get_server('testvarsrv')
        # elif operation == '21':
        #     comm_dev.set_server({'testvarsrv': 'testvaluesrv'})
        elif operation == '22':
            print "testvarcli= " + comm_dev.get_client('testvarcli')
        elif operation == '23':
            comm_dev.set_clyient({'testvarcli': 'testvaluecli'})
        elif operation == '24':
            comm_dev.install('wifi_enabler', )
        elif operation == '25':
            comm_dev.install_agent()
        elif operation == '26':
            comm_dev.uninstall('wifi_enabler')
        elif operation == '27':
            comm_dev.uninstall_agent()
        elif operation == '28':
            comm_dev.launch_default_activity('wifi_enabler')
        elif operation == '29':
            comm_dev.execute_agent()
        #DEPRECATED
        # elif operation == '30':
        #     comm_dev.build_apk_ruby()
        # elif operation == '31':
        #     commands.build_apk_ruby(rebuild=True)
        elif operation == '32':
            av = get_which_av()
            comm_dev.backup_app_data(av)
        elif operation == '33':
            av = get_which_av()
            comm_dev.restore_app_data(av)
        elif operation == '34':
            av = get_which_av()
            comm_dev.install_configuration(av)
        elif operation == '35':
            av = get_which_av()
            comm_dev.update_apk(av)
    if operation == '99':
        print "Operazioni terminate, cleaning time"
        comm_dev.reset_device()
    elif operation == '69':
        print "Operazioni terminate, esco senza pulire!"

    print "The end"

'''


commands.update()
commands.pull()
commands.push()



wifi
info_wifi_network
can_ping_google
check_su_permissions
check_infection
init_device
reset_device
update
pull
push
'''


def test_av(device, antivirus_apk_instance, results, av_update=True):
    print "##################################################"
    print "#### STAGE 1 : TESTING ANTIVIRUS %s ####" % antivirus_apk_instance.apk_file
    print "##################################################"

    dev = device.serialno

    print "#STEP 1.1: installing AV"
    antivirus_apk_instance.full_install(device)

    print "#STEP 1.2: starting AV"
    antivirus_apk_instance.start_default_activity(dev)

    if av_update:
        print "#STEP 1.3: going online for updates"
        wifiutils.start_wifi_open_network(dev)
        raw_input('Now update the av signatures and press Return to continue')
    else:
        print "#STEP 1.3: SKIPPED: no av update"

    print "#STEP 1.4: setting the local network to install agent"
    wifiutils.start_wifi_av_network(dev)

    print "#STEP 1.5: checking connection to TPLINK"
    wifiutils.start_wifi_av_network(dev)

    for i in range(1, 100):
        if "TP-LINK_9EF638" == wifiutils.info_wifi_network(dev):
            break
        time.sleep(2)

    print "Net is %s, we go on..." % wifiutils.info_wifi_network(dev)

    print "#STEP 1.6 WARNING INSTALLING AGENT"
    agent = apk_dataLoader.get_apk('agent')
    agent.install(dev)

    print "#STEP 1.7 WARNING LAUNCHING AGENT"
    agent.start_default_activity(dev)

    print "#STEP 1.8 MANUAL Invisibility check (NB: Check agent launch is no blocked by AV)"
    raw_input('Please check invisibility (and sync) and press Return to continue')

    print "#STEP 1.9 Uninstalling agent"
    agent.clean(dev)

    print "#STEP 1.10 Uninstalling AV"
    antivirus_apk_instance.clean(dev)

    return "Invisibility test terminated"


def do_test(device_id, av, av_update=True):
    # device_id = device #utils.get_deviceId(device)
    # assert device_id
    # assert len(device_id) >= 8

    with open('tmp/test-%s-%s.csv' % (device_id, av), 'wb') as csvfile:
        # write header
        devicelist = csv.writer(csvfile, delimiter=";", quotechar="|", quoting=csv.QUOTE_MINIMAL)

        # props = get_properties(device, "ro.product.manufacturer", "build.model", "build.selinux.enforce",
        # "build.version.release")
        props = utils.get_properties(device_id, av, "ro.product.manufacturer", "ro.product.model",
                                     "ro.build.selinux.enforce", "ro.build.version.release")

        # adds results to csv
        try:
            ret = test_device(device_id, av, props, av_update)
            props["return"] = ret
            print "return: %s " % ret
        except Exception, ex:
            traceback.print_exc(device_id)
            props['error'] = "%s" % ex

        print props
        devicelist.writerow(props.values())


def test_device(device_id, av, results, av_update=True):
    # extracts serial number (cannot pass an object to command line!)
    # dev = device.serialno

    # Starts av installation and stealth check)
    return test_av(device_id, apk_dataLoader.get_apk_av(av), results, av_update)


if __name__ == "__main__":
    main(sys.argv)
