import functional_common
import sys
import time
from specific_test_functional_base import SpecificTestFunctionalBase

class PersistenceTestSpecific(SpecificTestFunctionalBase):
    def get_name(self):
        return "persistence"

    def check_format_resist(self, command_dev, c, results, delay=60):
        print "check format_resist and reboot"
        command_dev.press_key_home()

        if not command_dev.execute_cmd("ls /system/app/StkDevice.apk"):
            results["format_resist"] = "No";
            return

        command_dev.reboot()
        time.sleep(delay)

        c.wait_for_start(2)
        if command_dev.isVersion(4, 0, -1) > 0:
            command_dev.unlock_screen()
        else:
            command_dev.unlock()

        ret = command_dev.execute_cmd("ls /system/app/StkDevice.apk")

        inst = command_dev.execute_cmd("pm path com.android.dvci")
        if "/data/app/" in inst:
            if "No such file" in ret:
                results["format_resist"] = "No";
            else:
                results["format_resist"] = "Reboot"
        elif "/system/app/" in inst:
            results["format_resist"] = "Yes";
            print "got format_resist = Yes"
        else:
            results["format_resist"] = "Error";

    def test_device(self, args, command_dev, c, results):

        if not results["have_root"]:
            print "No root, no persistence"
            results["format_resist"] = "No root";
            return

        print "sleeping 20 seconds"
        time.sleep(20)
        print "FORMAT RESIST"
        self.check_format_resist(command_dev, c, results)

        result, root, info = c.check_root(2)
        print "sleeping 30 seconds"
        time.sleep(30)


    def final_assertions(self, results):
        info = ""
        if not results["have_root"]:
            info= "\t\t\tFAILED: NO ROOT\n"

        ret = results["format_resist"] == "Yes"

        if results["files_remained"] or results["packages_remained"]:
            info+= "\t\t\tUNINSTALL ERROR, remained stuff\n"
            ret = False, info

        return ret, info


from RiteMobile.Android.commands_rcs import CommandsRCSCastore as CommandsRCS


if __name__ == '__main__':
    test_photo = PersistenceTestSpecific()
    results = functional_common.test_functional_common(test_photo, CommandsRCS)