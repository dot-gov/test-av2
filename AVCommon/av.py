import yaml

__author__ = 'mlosito'


class AV(object):

    scan_placeholder = "<*FOLDER*>"

    def __init__(self, av_id):
        self.name = None
        self.important = None
        self.level = None
        self.iso_level = None
        self.os = None
        self.vm_path = None
        self.full = None
        self.license_expiry_date = None
        self.bits = None
        self.cloud = None
        self.firewall = None
        self.update_cmd = None
        self.last_updated_date = None
        self.scan_cmd = None

        error = self.load(av_id)
        if error:
            print error

    def load(self, av_id):
        filename = './AVCommon/conf/av/%s.yaml' % av_id
        try:
            fil = open(filename)
            av_data = yaml.load(fil)
        except:
            return "Av configuration not found! Tried to open file: %s" % filename
        try:
            self.name = av_data['name']
            self.important = av_data['important']
            self.level = av_data['level']
            self.iso_level = av_data['iso_level']
            self.os = av_data['os']
            self.vm_path = av_data['vm_path']
            self.full = av_data['full']
            self.license_expiry_date = av_data['license_expiry_date']
            self.bits = av_data['bits']
            self.cloud = av_data['cloud']
            self.firewall = av_data['firewall']
            self.update_cmd = av_data['update_cmd']
            self.last_updated_date = av_data['last_updated_date']
            self.scan_cmd = av_data['scan_cmd']

            return None
        except:
            return "Invalid configuration in file %s" % filename

    def scan_cmd_replaced(self, check_dir):
        if self.scan_cmd:
            return self.scan_cmd.replace(self.scan_placeholder, check_dir)
        else:
            return None

class UndefinedAV(Exception):
    pass