__author__ = 'mlosito'

import zipfile
import os

def unzip(filename, fdir, logging_function):
    zfile = zipfile.ZipFile(filename)
    names = []
    for name in zfile.namelist():
        if os.path.exists(name):
            os.remove(name)
        (dirname, filename) = os.path.split(name)
        logging_function("- Decompress: %s / %s" % (fdir, filename))
        zfile.extract(name, fdir)
        names.append('%s/%s' % (fdir, name))
    return names