import functional_common
import sys
import time
from specific_test_functional_base import SpecificTestFunctionalBase

class PersistenceTestSpecific(SpecificTestFunctionalBase):
    def get_info(self):
        return """ Builds a PERSITENCE SILENCE and check that:
         - Persistence is installed
         - Everything is correctly uninstalled
        """

    def get_name(self):
        return "persistence"

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