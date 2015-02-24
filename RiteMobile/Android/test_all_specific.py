import functional_common
import time


class AllTestSpecific(functional_common.Check):

    def __init__(self, test_list):
        self.test_list = test_list

    def test_device(self, args, command_dev, c, results):
        print "ALL"

        exceptions = {}
        for t in self.test_list:
            command_dev.report("testing " + t.get_name())

            try:
                t.test_device(args, command_dev, c, results)
            except Exception, ex:
                print ex
                exceptions[t.get_name()] = ex

        results['exception'] = exceptions

    def get_name(self):
        return "all"

    def final_assertions(self, results):
        ret = {}
        for t in self.test_list:
            name = t.get_name()
            print "testing: " + name
            try:
                r = t.final_assertions(results)
            except Exception, ex:
                print ex
                r = False
            print "ASSERTION: %s %s" % (name, r)
            ret[name] = r

        return all(ret.values())
