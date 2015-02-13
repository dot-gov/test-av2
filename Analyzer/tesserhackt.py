__author__ = 'mlosito'

from PIL import Image

import glob
import os
import socket
import subprocess

from ocrdict import OcrDict

debug = True


def main():
    process()


def process(av="*", num="*"):
    prefix = '/home/avmonitor/logs/'
    hostname = socket.gethostname()
    if hostname == 'rite':
        prefix = '/home/avmonitor/Rite/logs/'
        # to test
        #prefix = '/home/avmonitor/AVTest2_old/logs/'

    print("av = %s, nume = %s" % (av, num))

    #if num is not * it gets only the file with the specified number
    filelist = sorted(glob.glob(prefix + "*/crop/%s/%s.png" % (av, num)))  # key=os.path.getmtime, reverse=True)

    if not len(filelist):
        print("No crop file found.")
        return "NO CROP FOUND", "", ""

    if debug or (av == "*" and num == "*"):
        return processlist(prefix, filelist)
    else:
        return processlist(prefix, filelist[:1])


def processlist(prefix, filelist):
    print("Expanding dictionary..."),

    ocrd = OcrDict()

    print("...expanded from %s to  %s words" % (ocrd.original_size, ocrd.size))

    # full_text = "Tesseract output\n"
    # print("Working..."),

    for file_input in filelist:
        file_input_full = os.path.join(prefix, file_input)
        text = parse_crop(file_input_full)
        result, outtext, word, description = ocrd.parseresult(text)
        print ("File: %s -> %s%s" % (file_input, result, description))
        if debug:
            print "Fulltext from tesseract = %s" % text
        thumb_filename = ""

        # saves
        if result in ['UNKNOWN', 'BAD', 'CRASH', "NO_TEXT"]:
            thumb_filename = save_thumbnail(file_input_full)

        if len(filelist) == 1:
            return result, word, thumb_filename


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


def is_text_ok(text):
    return True


def save_thumbnail(crop_filename):
    im = Image.open(crop_filename)
    out_filename = crop_filename.replace(".png", "_thumb.jpg")
    im.save(out_filename, quality=80, optimize=True)
    return out_filename


if __name__ == "__main__":
    main()