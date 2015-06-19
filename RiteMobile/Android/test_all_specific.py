import functional_common
import time


class AllTestSpecific(functional_common.TestFunctionalBase):

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

        ret = True
        info = ""
        for t in self.test_list:
            name = t.get_name()
            print "testing: " + name
            try:
                r,i = t.final_assertions(results)
            except Exception, ex:
                print ex
                i = ex
                r = False
            print "ASSERTION: %s %s %s" % (name, r, i)

            ret = ret and r
            if r and not i:
                i = ""
            info += "\n\t\t%s: %s\n%s" % (name, r, i)

        return ret, info
