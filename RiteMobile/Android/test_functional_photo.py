import functional_common
import time
from specific_test_functional_base import SpecificTestFunctionalBase
from RiteMobile.Android.commands_rcs import CommandsRCSCastore as CommandsRCS


class PhotoTestSpecific(SpecificTestFunctionalBase):
    def get_info(self):
        return """ Builds a silent, with PHOTO enabled and check that:
         - Photo are correctly extracted
         - Everything is correctly uninstalled
        """

    def test_device(self, args, command_dev, c, results):
        print "PHOTO"

        self.check_photo(command_dev)

    def get_name(self):
        return "photo"

    def check_photo(self, command_dev):
        command_dev.execute_camera()

        time.sleep(20)
        pass

    def final_assertions(self, results):
        print "evidence_types_last: ", results["evidence_types_last"]
        ret = "photo" in results["evidence_types_last"]
        info = ""

        return ret, info


if __name__ == '__main__':
    test_photo = PhotoTestSpecific()
    results = functional_common.test_functional_common(test_photo, CommandsRCS)