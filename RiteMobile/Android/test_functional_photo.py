import functional_common
import time

from RiteMobile.Android.commands_rcs import CommandsRCSCastore as CommandsRCS


class PhotoTestSpecific(functional_common.Check):

    def test_device(self, args, command_dev, c, results):
        print "PHOTO"

        self.check_photo(command_dev)

    def get_name(self):
        return "photo"

    def check_photo(self, command_dev):
        command_dev.execute_camera()

        time.sleep(10)
        pass

    def final_assertions(self, results):
        print "evidence_types_last: ", results["evidence_types_last"]
        ret = "photo" in results["evidence_types_last"]
        return ret


if __name__ == '__main__':
    test_photo = PhotoTestSpecific()
    results = functional_common.test_functional_common(test_photo, CommandsRCS)