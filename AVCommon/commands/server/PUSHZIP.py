__author__ = 'mlosito'

from AVCommon import utils

report_level = 2

#config.verbose = True


def execute(vm, protocol, args):
    return utils.pushzip(vm, args)
