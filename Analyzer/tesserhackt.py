__author__ = 'mlosito'

from PIL import Image

import glob
import os
import socket
import subprocess

from ocrdict import OcrDict

debug = False

log_dir = '/home/avmonitor/logs/'
hostname = socket.gethostname()
if hostname == 'rite':
    log_dir = '/home/avmonitor/Rite/logs/'
    # to test
    #prefix = '/home/avmonitor/AVTest2_old/logs/'


def main():
    process()


#process is a wrapper which finds the filenames and passes them to processlist
def process(av="*", num="*", ocrd=None):

    print("av = %s, nume = %s" % (av, num))

    #if num is not * it gets only the file with the specified number
    filelist = sorted(glob.glob(log_dir + "*/crop/%s/%s.png" % (av, num)))  # key=os.path.getmtime, reverse=True)

    if not len(filelist):
        print("No crop file found.")
        return "NO CROP FOUND", "", ""

    return processlist(log_dir, filelist, ocrd)

    # if debug or (av == "*" and num == "*"):
    #     #processes all
    #     return processlist(prefix, filelist, ocrd)
    #     #it should process only one image but in rare case if there are multiple images with the same number, may be multiple
    # else:
    #     # print filelist[:1]
    #     return processlist(prefix, filelist, ocrd)


def processlist(prefix, filelist, ocrd, av=None):
    result_list = []
    if ocrd is None:
        ocrd = OcrDict()

    for file_input in filelist:
        file_input_full = os.path.join(prefix, file_input)
        text = parse_crop(file_input_full)
        result, outtext, word, description = ocrd.parseresult(text)
        print ("File: %s -> %s%s" % (file_input, result, description))
        if debug:
            print "Fulltext from tesseract = %s" % text
        thumb_filename = ""

        # saves
        if not av:
            if result in ['UNKNOWN', 'BAD', 'CRASH', "NO_TEXT"]:
                thumb_filename = save_thumbnail(file_input_full)
        #if called from tesserest we should save the image!
        else:
            out_dir = "%spopup_thumbs/%s/" % (log_dir, av)
            if result in ['UNKNOWN', 'BAD', 'CRASH']:
                out_dir += "OK/"
                thumb_filename = save_thumbnail(file_input_full, out_dir)
            elif result in ['GOOD', "NO_TEXT"]:
                out_dir += "NOK/"
                thumb_filename = save_thumbnail(file_input_full, out_dir)

        if len(filelist) == 1:
            return result, word, thumb_filename
        else:
            if result in ['UNKNOWN', 'BAD', 'CRASH']:
                return result, word, thumb_filename
            else:
                result_list.append([result, word, thumb_filename])

    #I came here if the filelist is multiple and has non bad/crash/unknown
    #i return just the first result
    return result_list[0]


def parse_crop(crop_filename):
    im = Image.open(crop_filename)
    out_filename = crop_filename.replace(".png", ".jpg")
    # from 72dpi to about 300dpi
    im = im.resize((im.size[0]*4, im.size[1]*4), Image.ANTIALIAS)

    im.save(out_filename, dpi=(300, 300))
    # im1 = im.convert('1')
    # im1.save("out1.jpg", dpi=(300, 300))
    # imL = im.convert('L')
    # imL.save("outL.jpg", dpi=(300, 300))

    text = exec_tesseract(out_filename)

    return text
    # return is_text_ok(text)


def exec_tesseract(out_filename):
    proc = subprocess.Popen(["tesseract", out_filename, "stdout"], stdout=subprocess.PIPE)
    comm = proc.communicate()
    return str(comm[0])


#if you want the thumb in another dir prlease provide a FULL out_dir name
#it will becreated if does not exists
def save_thumbnail(crop_filename, out_dir=None):
    if out_dir:
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

    im = Image.open(crop_filename)

    if out_dir:
        crop_filename = os.path.join(out_dir, os.path.basename(crop_filename))

    out_filename = crop_filename.replace(".png", "_thumb.jpg")
    i = 0
    while os.path.exists(out_filename):
        out_filename = crop_filename.replace(".png", "_thumb_%s.jpg" % i)
        i += 1

    im.save(out_filename, quality=80, optimize=True)
    return out_filename


if __name__ == "__main__":
    main()