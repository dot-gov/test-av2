import functional_common
import sys

from RiteMobile.Android.commands_rcs import CommandsRCSCastore as CommandsRCS


class TestSpecific(functional_common.Check):
    def test_device(self, args, command_dev, c, results):
        self.check_evidences(command_dev, c, results, "_first")
        print "PHOTO"
        self.check_photo(results)

    def get_config(self):
        return open('assets/config_mobile_photo.json').read()

    def check_photo(self, results):
        self.check_evidences_present()
        pass

    def final_assertions(self, results):
        return True


if __name__ == '__main__':
    test_photo = TestSpecific()
    results = functional_common.test_functional_common(test_photo, CommandsRCS)