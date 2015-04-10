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
                print "Saving thumbnail"
                thumb_filename = save_thumbnail(file_input_full)
        #if called from tesserest we should save the image!
        else:
            out_dir = "%spopup_thumbs/%s/" % (log_dir, av)
            print "Saving thumbnail to: %s" % out_dir
            if result in ['UNKNOWN', 'BAD', 'CRASH']:
                out_dir += "NOK/"
                thumb_filename = save_thumbnail(file_input_full, out_dir)
            elif result in ['GOOD', "NO_TEXT"]:
                out_dir += "OK/"
                thumb_filename = save_thumbnail(file_input_full, out_dir)

        print "Thumbnail saved or saving skipped"

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
    try:
        im = Image.open(crop_filename)
        #jpg and png are supported
        if ".jpg" in crop_filename:
            out_filename = crop_filename.replace(".jpg", "_up.jpg")
        else:
            out_filename = crop_filename.replace(".png", "_up.jpg")
        # from 72dpi to about 300dpi
        im = im.resize((im.size[0]*4, im.size[1]*4), Image.ANTIALIAS)

        im.save(out_filename, dpi=(300, 300))
        print "Saved upscaled image"
        # im1 = im.convert('1')
        # im1.save("out1.jpg", dpi=(300, 300))
        # imL = im.convert('L')
        # imL.save("outL.jpg", dpi=(300, 300))

        text = exec_tesseract(out_filename)
        print text
        return text
    except IOError:
        print "Invalid image file. Returning void text."
        return ""

    # return is_text_ok(text)


def exec_tesseract(out_filename):
    if "avmaster" == socket.gethostname():
        txt_out = out_filename.replace(".jpg", "")
        proc = subprocess.Popen(["tesseract", out_filename, txt_out, "nobatch", "ascii_ml"], stdout=subprocess.PIPE)
        comm = proc.communicate()
        print "Tesseract execution completed."
        f = open(txt_out+".txt", "r")
        return f.read()
    else:
        proc = subprocess.Popen(["tesseract", out_filename, "stdout", "ascii_ml"], stdout=subprocess.PIPE)
        comm = proc.communicate()
        print "Tesseract execution completed."
        return str(comm[0])


#if you want the thumb in another dir prlease provide a FULL out_dir name
#it will becreated if does not exists
def save_thumbnail(crop_filename, out_dir=None):
    if out_dir:
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
    try:
        print "Opening image %s to create thumbnail" % crop_filename
        im = Image.open(crop_filename)
        print "Opened image %s to create thumbnail" % crop_filename
        if out_dir:
            crop_filename = os.path.join(out_dir, os.path.basename(crop_filename))

        #if the file is a jpg I rename it to png so thumbnail is saved correctly
        #jpg and png are supported
        if ".jpg" in crop_filename:
            out_filename = crop_filename.replace(".jpg", "_thumb.jpg")
        else:
            out_filename = crop_filename.replace(".png", "_thumb.jpg")

        i = 0
        while os.path.exists(out_filename):
            if ".jpg" in crop_filename:
                out_filename = crop_filename.replace(".jpg", "_thumb_%s.jpg" % i)
            else:
                out_filename = crop_filename.replace(".png", "_thumb_%s.jpg" % i)
            i += 1
        print "I will save thumbnail %s" % out_filename
        im.save(out_filename, quality=75)
        print "Thumbnail saved!"
        return out_filename
    except IOError:
        print "Cannot save thumbnail. Probably pil cannot convert image. Using original file."
        return crop_filename

if __name__ == "__main__":
    main()