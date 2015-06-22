import functional_common
import sys
import time

from specific_test_functional_base import SpecificTestFunctionalBase
class MeltTestSpecific(SpecificTestFunctionalBase):

    def get_info(self):
        return """ Builds a persistent MELT and check that:
         - Persistence is installed
         - Everything is correctly uninstalled
        """

    def get_name(self):
        return "melt"

    def want_persist(self):
        return False

    def want_admin(self):
        return False


    def test_device(self, args, command_dev, c, results):
        if not results["have_root"]:
            print "No root, no persistence"
            results["format_resist"] = "No root";
            return

        print "sleeping 20 seconds"
        time.sleep(20)
        print "FORMAT RESIST"
        self.check_format_resist(command_dev, c, results)

    def melting_app(self):
        return "assets/DailyBible.apk"

    def final_assertions(self, results):
        info = ""
        ret = results["format_resist"] == "Yes"
        if not results.get("have_root"):
            info= "\t\t\tFAILED: NO ROOT\n"
            ret = False

        if results["files_remained"] or results["packages_remained"]:
            info+= "\t\t\tUNINSTALL ERROR, remained stuff\n"
            ret = False

        return ret, info


from RiteMobile.Android.commands_rcs import CommandsRCSCastore as CommandsRCS


if __name__ == '__main__':
    test_photo = MeltTestSpecific()
    results = functional_common.test_functional_common(test_photo, CommandsRCS)