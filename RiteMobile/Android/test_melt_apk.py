import argparse
import collections
import traceback
from RiteMobile.Android.commands_device import CommandsDevice
from RiteMobile.Android.commands_rcs import CommandsRCSPolluce

from AVCommon import logger
logger.init()

__author__ = 'zeno'

def parse_args():
    parser = argparse.ArgumentParser(description='RiteMobile Android melt test.')
    parser.add_argument('-b', '--build', required=False, action='store_true',
                        help="Rebuild apk")
    parser.add_argument('-i', '--interactive', required=False, action='store_true',
                        help="Interactive execution")
    parser.add_argument('-f', '--fastnet', required=False, action='store_true',
                        help="Install fastnet")
    parser.add_argument('-r', '--reboot', required=False, action='store_true',
                        help="Install fastnet")

    args = parser.parse_args()

    return args


def main():
    # from AVCommon import logger
    # logger.init()

    command_dev = CommandsDevice()

    args = parse_args()
    results = collections.OrderedDict()

    try:
        device_id = command_dev.get_dev_deviceid()
        commands_rcs = CommandsRCSPolluce(login_id=0, device_id=device_id)
        with commands_rcs as c:
            ret = c.build_melt_apk(  melt_file = "assets/melt/DailyBible.apk" )


    except Exception, ex:
        print ex
        traceback.print_exc()
        results['exception'] = ex

    print results


    print "Fine."


if __name__ == "__main__":
    main()
