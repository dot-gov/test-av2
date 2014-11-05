#required: https://code.google.com/p/androguard/wiki/RE

import os
import os.path
from androguard.core.bytecodes import apk

def infoapk(apk_file):
    try:
        a = apk.APK(apk_file)
        ret="target: %s min: %s max: %s" % (a.get_target_sdk_version(), a.get_min_sdk_version(), a.get_max_sdk_version())
    except:
        ret = ""
    return ret

infos = []

apks = os.listdir("/Volumes/SHARE/QA/SVILUPPO/PlayStoreApps")
apks.sort()

f=open("apks.infos.txt", "w")

for a in apks:
    file="/Volumes/SHARE/QA/SVILUPPO/PlayStoreApps/" + a
    package = a.rstrip(".apk")

    repack = "No"
    dir ="out/" + package
    os.system("java -jar /Users/zeno/Reversing/Android/apktool/2.0/apktool_2.0.0rc2.jar -f -o out/%s d %s" % (package,file))
    if os.path.exists(dir):
        repack = "Uninst"
        os.system("/Users/zeno/bin/pack.sh out/%s" % package)

    aligned = dir + ".align.apk"

    if os.path.exists(aligned):
        os.remove(aligned)

        repack = "Yes"

    if os.path.exists(dir):
        os.removedirs(dir)

    info = "%s (%s) repack: %s -> %s\n" % (a, os.stat(file).st_size, repack, infoapk(file))
    infos += info
    print info
    f.write(info)
    f.flush()


f.close()