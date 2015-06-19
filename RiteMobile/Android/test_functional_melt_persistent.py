import functional_common
import sys
import time

from specific_test_functional_base import SpecificTestFunctionalBase
class RootTestSpecific(SpecificTestFunctionalBase):
    def get_name(self):
        return "root"

    def want_persist(self):
        return False

    def want_admin(self):
        return False

    def test_device(self, args, command_dev, c, results):
        pass


    def final_assertions(self, results):
        info = ""
        ret = True
        if not results.get("have_root"):
            info= "\t\t\tFAILED: NO ROOT\n"
            ret = False

        if results["files_remained"] or results["packages_remained"]:
            info+= "\t\t\tUNINSTALL ERROR, remained stuff\n"
            ret = False

        return ret, info


from RiteMobile.Android.commands_rcs import CommandsRCSCastore as CommandsRCS


if __name__ == '__main__':
    test_photo = RootTestSpecific()
    results = functional_common.test_functional_common(test_photo, CommandsRCS)