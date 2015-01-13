__author__ = 'mlosito'


class ResultStates(object):
    FAILED = ["FAILED", 100]
    NO_SYNC = ["NO_SYNC", 70]
    CROP = ["CROP", 50]
    NOT_APPLICABLE = ["NOT_APPLICABLE", 1]
    PASSED = ["PASSED", 0]
    NONE = ["NONE", None]

    def get_state_from_content(self, content):
        if content in self.FAILED:
            return self.FAILED
        if content in self.NO_SYNC:
            return self.NO_SYNC
        if content in self.CROP:
            return self.CROP
        if content in self.NOT_APPLICABLE:
            return self.NOT_APPLICABLE
        if content in self.PASSED:
            return self.PASSED
        if content in self.NONE:
            return self.NONE