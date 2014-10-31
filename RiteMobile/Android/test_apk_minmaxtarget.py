#required: https://code.google.com/p/androguard/wiki/RE

import os
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
	info = "%s -> %s\n" % (a, infoapk("/Volumes/SHARE/QA/SVILUPPO/PlayStoreApps/" + a))
	infos += info
	print info
	f.write(info)

f.close()
