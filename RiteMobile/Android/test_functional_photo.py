import functional_common
import time

from RiteMobile.Android.commands_rcs import CommandsRCSCastore as CommandsRCS


class TestSpecific(functional_common.Check):

    def test_device(self, args, command_dev, c, results):
        print "PHOTO"

        self.check_photo(command_dev)

    def get_config(self):
        return open('assets/config_mobile_photo.json').read()

    def check_photo(self, command_dev):
        command_dev.execute_camera()

        time.sleep(10)
        pass

    def final_assertions(self, results):
        ret = "photo" in results["evidence_types_last"]
        return ret


if __name__ == '__main__':
    test_photo = TestSpecific()
    results = functional_common.test_functional_common(test_photo, CommandsRCS)