import argparse
import collections
import glob
from random import shuffle
import traceback
import os
import time
from urllib2 import HTTPError

from RiteMobile.Android.commands_device import CommandsDevice
from RiteMobile.Android.commands_rcs import CommandsRCSCastore
from RiteMobile.Android.commands_rcs import CommandsRCSPolluce
from AVCommon import logger
from RiteMobile.Android.utils import androguardutils


logger.init()

__author__ = 'zeno'

apk_share_dir = "/Users/mlosito/Sviluppo/PlayStoreApps/"  # "/Volumes/SHARE/QA/SVILUPPO/PlayStoreApps/"

build_melt_dir = "build_melt/"

# av_list = ["com.antivirus", "com.avast.android", "com.qihoo.security", "com.lookout"]
av_list = []

server = "polluce"

# test_to_run = ["melt_server", "zip_run"]
test_to_run = ["melt_server"]
# test_to_run = ["zip_run"]

#max retries for a single build (in case of timeout)
max_timeout_retries = 1

#max number of app to process
max_test_iterations = 9999

filter_string = ""   # "com.amazon.kindle"  # "com.utorrent.client-2.20.apk"  # "com.bigduckgames.flow"  # example: "com.amazon.kindle"  #empty string gets all apks
# filter_string = ""  #gets all apks

result_installation = []

uninstall = False

# these are ok
# these_does_not_work_list = ['com.google.android.voicesearch-4.0.0.apk', 'Maps.apk', 'com.badoo.mobile-2.52.1.apk',
#                             'com.google.android.apps.maps-8.4.1.apk', 'com.roidapp.photogrid-4.792.apk', 'tunein.player-12.8.apk',
#                             'com.sgiggle.production-3.10.106185.apk', 'com.google.android.tts-3.2.12.1369973.arm.apk',
#                             'com.cleanmaster.mguard-5.8.6.apk', 'de.lotum.whatsinthefoto.us-4.2.apk', 'com.snapchat.android-5.0.38.2.apk']
#
# unknown = ['com.gameloft.android.ANMP.GloftDMHM-2.2.1f.apk', 'com.amazon.kindle-4.7.1.1.apk', 'com.touchtype.swiftkey-5.0.5.95.apk',
#            'com.yahoo.mobile.client.android.mail-4.6.2.apk', 'com.bbm-2.4.0.11.apk', 'com.kiloo.subwaysurf-1.30.0.apk', 'com.evernote-6.0.2.apk',
#            'eu.nordeus.topeleven.android-2.32.1.apk', 'jp.naver.SJLGPP-2.1.4.apk', 'com.ebay.mobile-2.7.0.142.apk',
#            'com.outfit7.talkingangelafree-2.3.apk', 'com.venticake.retrica-2.2.3.apk', 'com.seventeenbullets.android.island-2.8.12.apk',
#            'com.myfitnesspal.android-3.5.2.apk', 'com.sirma.mobile.bible.android-5.3.0.apk', 'com.etermax.preguntados.lite-1.9.1.apk',
#            'logos.quiz.companies.game-16.2.apk', 'com.skype.raider-5.0.0.52727.apk', 'com.dragonplay.liveholdempro-6.29.apk',
#            'com.utorrent.client-2.20.apk', 'com.viber.voip-5.0.2.12.apk', 'com.miniclip.plagueinc-1.9.1.apk', 'com.antivirus-4.1.2.apk',
#            'com.rovio.angrybirdsstarwars.ads.iap-1.5.3.apk']
#
# these_works_list = ['com.sonyericsson.extras.liveware-5.7.11.130.apk', 'com.zeptolab.ctr.ads-2.4.4.apk', 'com.hotdog.tinybattle-2.2.3.apk',
#                     'com.whatsapp-2.11.399.apk', 'com.estrongs.android.pop-3.2.1.2.apk', 'com.shazam.android-4.10.0-14102116-bf48e17.apk',
#                     'mobi.mgeek.TunnyBrowser-11.2.6.apk', 'com.robtopx.geometryjumplite-1.81.apk', 'air.au.com.metro.DumbWaysToDie-1.6.apk',
#                     'com.avast.android.mobilesecurity-3.0.7864.apk', 'com.outfit7.talkingnewsfree-2.1.apk', 'com.gau.go.launcherex-5.08.apk',
#                     'com.sundaytoz.mobile.anipang2.google.kakao.service-1.0.35.apk', 'com.jb.gosms-6.0.apk',
#                     'com.midasplayer.apps.papapearsaga-1.22.0.apk', 'com.omgpop.dstfree-2.333.302.apk', 'me.pou.app-1.4.61.apk',
#                     'com.ea.games.simsfreeplay_row-5.8.0.apk', 'jp.naver.linecamera.android-8.6.3.apk', 'com.wooga.diamonddash-3.4.apk',
#                     'com.soundcloud.android-14.10.01-27.apk', 'com.nordcurrent.Games101-1.3.30.apk',
#                     'com.melodis.midomiMusicIdentifier.freemium-6.2.0.apk', 'com.cjenm.ModooMarbleKakao-1.9.24.apk',
#                     'com.midasplayer.apps.bubblewitchsaga2-1.11.4.apk', 'com.aviary.android.feather-3.5.0.apk', 'com.king.petrescuesaga-1.30.4.apk',
#                     'vStudio.Android.Camera360-5.4.5.apk', 'com.dianxinos.optimizer.duplay-2.1.2.apk',
#                     'com.zynga.FarmVille2CountryEscape-2.1.127.apk', 'com.dataviz.docstogo-4.001.apk', 'com.linecorp.LGRGS-1.1.8.apk',
#                     'com.mobilityware.solitaire-3.1.2.apk', 'com.bestcoolfungames.antsmasher-7.2.apk', 'com.accuweather.android-3.3.2.7.apk',
#                     'com.ansangha.drdriving-1.38.apk', 'com.kiragames.unblockmefree-1.5.0.0.apk', 'com.sec.chaton-1.11.2.apk',
#                     'es.socialpoint.DragonCity-2.11.apk', 'com.bsb.hike-3.3.5.apk', 'ch.smalltech.ledflashlight.free-1.68.apk',
#                     'com.forshared-2.5.10.apk', 'com.leftover.CoinDozer-14.2.apk', 'com.linktomorrow.candypang-1.27.apk',
#                     'com.google.android.youtube-5.10.3.5.apk', 'com.pinterest-3.5.1.apk', 'com.picsart.studio-4.6.12.apk',
#                     'com.instagram.android-6.9.1.apk', 'net.mobilecraft.realbasketball-1.8.apk', 'com.amazon.mp3-4.1.1.apk', 'YouTube.apk',
#                     'Hangouts.apk', 'com.outfit7.talkingben-3.1.apk', 'com.outfit7.talkingtom2free-4.6.apk', 'com.qihoo.security-2.1.0.apk',
#                     'com.fdgentertainment.paperama-1.3.6.apk', 'com.king.candycrushsaga-1.39.4.apk', 'com.whatsapp.wallpaper-2.apk',
#                     'com.threed.bowling-2.6.apk', 'com.blurb.checkout-1.0.apk', 'com.lookout-9.6.4-f3c9c32.apk',
#                     'goldenshorestechnologies.brightestflashlight.free-2.4.2.apk', 'com.google.android.marvin.talkback-3.1.1_r68.apk',
#                     'com.julian.fastracing-1.1.apk', 'com.dsi.ant.plugins.antplus-3.1.0.apk', 'com.melimots.WordSearch-1.14.apk',
#                     'com.google.android.videos-2.0.21.apk', 'com.outfit7.talkingpierrefree-3.1.apk', 'Music2.apk',
#                     'com.yahoo.mobile.client.android.im-1.8.8.apk', 'flipboard.app-1.9.6.apk', 'com.fdgentertainment.bananakong-1.8.apk',
#                     'com.opera.mini.android-7.6.1.apk', 'Velvet.apk', 'com.linktomorrow.windrunner-3.82.apk',
#                     'com.sec.android.fwupgrade-1.2.3717.apk', 'com.game.SkaterBoy-1.6.apk', 'com.fingersoft.hillclimb-1.18.0.apk',
#                     'com.ogqcorp.bgh-3.6.4.apk', 'com.opera.browser-25.0.1619.84037.apk', 'com.linecorp.LGCOOKIE-2.0.5.apk',
#                     'com.zeptolab.ctr2.f2p.google-1.1.7.apk', 'com.kfactormedia.mycalendarmobile-3.02.apk', 'net.mobigame.zombietsunami-1.6.46.apk',
#                     'com.dhqsolutions.enjoyphoto-2.0.0.apk', 'com.google.zxing.client.android-4.7.0.apk', 'com.nekki.vector-1.1.0.apk',
#                     'GoogleTTS.apk', 'com.google.android.street-1.8.1.2.apk', 'Street.apk', 'com.rechild.advancedtaskkiller-2.0.3B203.apk',
#                     'LatinImeGoogle.apk', 'com.adobe.reader-11.7.0.apk', 'com.dsi.ant.service.socket-4.7.0.apk', 'com.sec.spp.push-1.2.9.1.apk',
#                     'com.socialnmobile.dictapps.notepad.color.note-3.9.60.apk', 'com.dropbox.android-2.1.11.apk', 'com.easy.battery.saver-3.4.1.apk',
#                     'com.sec.pcw-1.0.1943.apk', 'com.umonistudio.tile-2.9.5.apk', 'com.imangi.templerun-1.0.8.apk',
#                     'com.google.android.apps.translate-3.0.15.apk', 'PlusOne.apk', 'com.estoty.game2048-6.22.apk', 'com.devexpert.weather-4.1.1.apk',
#                     'com.natenai.glowhockey-1.2.16.apk', 'com.duolingo-2.9.0.apk', 'com.imdb.mobile-5.0.3.105030410.apk',
#                     'com.NextFloor.DragonFlightKakao-2.6.2.apk', 'com.disney.WMWLite-1.9.1.apk', 'com.bigduckgames.flow-2.8.apk']
#
# to_test_list = ['Hangouts.apk', 'Maps.apk', 'YouTube.apk', 'air.au.com.metro.DumbWaysToDie-1.6.apk', 'ch.smalltech.ledflashlight.free-1.68.apk',
#                 'com.accuweather.android-3.3.2.7.apk', 'com.amazon.kindle-4.7.1.1.apk', 'com.amazon.mp3-4.1.1.apk', 'com.ansangha.drdriving-1.38.apk',
#                 'com.antivirus-4.1.2.apk', 'com.avast.android.mobilesecurity-3.0.7864.apk', 'com.aviary.android.feather-3.5.0.apk',
#                 'com.badoo.mobile-2.52.1.apk', 'com.bbm-2.4.0.11.apk', 'com.bestcoolfungames.antsmasher-7.2.apk', 'com.bsb.hike-3.3.5.apk',
#                 'com.cjenm.ModooMarbleKakao-1.9.24.apk', 'com.cleanmaster.mguard-5.8.6.apk', 'com.dataviz.docstogo-4.001.apk',
#                 'com.dianxinos.optimizer.duplay-2.1.2.apk', 'com.dragonplay.liveholdempro-6.29.apk', 'com.ea.games.simsfreeplay_row-5.8.0.apk',
#                 'com.ebay.mobile-2.7.0.142.apk', 'com.estrongs.android.pop-3.2.1.2.apk', 'com.etermax.preguntados.lite-1.9.1.apk',
#                 'com.evernote-6.0.2.apk', 'com.forshared-2.5.10.apk', 'com.gameloft.android.ANMP.GloftDMHM-2.2.1f.apk',
#                 'com.gau.go.launcherex-5.08.apk', 'com.google.android.apps.maps-8.4.1.apk', 'com.google.android.tts-3.2.12.1369973.arm.apk',
#                 'com.google.android.voicesearch-4.0.0.apk', 'com.google.android.youtube-5.10.3.5.apk', 'com.hotdog.tinybattle-2.2.3.apk',
#                 'com.instagram.android-6.9.1.apk', 'com.jb.gosms-6.0.apk', 'com.kiloo.subwaysurf-1.30.0.apk', 'com.king.petrescuesaga-1.30.4.apk',
#                 'com.kiragames.unblockmefree-1.5.0.0.apk', 'com.leftover.CoinDozer-14.2.apk', 'com.linecorp.LGRGS-1.1.8.apk',
#                 'com.linktomorrow.candypang-1.27.apk', 'com.melodis.midomiMusicIdentifier.freemium-6.2.0.apk',
#                 'com.midasplayer.apps.bubblewitchsaga2-1.11.4.apk', 'com.midasplayer.apps.papapearsaga-1.22.0.apk',
#                 'com.miniclip.plagueinc-1.9.1.apk', 'com.mobilityware.solitaire-3.1.2.apk', 'com.myfitnesspal.android-3.5.2.apk',
#                 'com.nordcurrent.Games101-1.3.30.apk', 'com.omgpop.dstfree-2.333.302.apk', 'com.outfit7.talkingangelafree-2.3.apk',
#                 'com.outfit7.talkingben-3.1.apk', 'com.outfit7.talkingnewsfree-2.1.apk', 'com.outfit7.talkingtom2free-4.6.apk',
#                 'com.picsart.studio-4.6.12.apk', 'com.pinterest-3.5.1.apk', 'com.qihoo.security-2.1.0.apk', 'com.robtopx.geometryjumplite-1.81.apk',
#                 'com.roidapp.photogrid-4.792.apk', 'com.rovio.angrybirdsstarwars.ads.iap-1.5.3.apk', 'com.sec.chaton-1.11.2.apk',
#                 'com.seventeenbullets.android.island-2.8.12.apk', 'com.sgiggle.production-3.10.106185.apk',
#                 'com.shazam.android-4.10.0-14102116-bf48e17.apk', 'com.sirma.mobile.bible.android-5.3.0.apk', 'com.skype.raider-5.0.0.52727.apk',
#                 'com.snapchat.android-5.0.38.2.apk', 'com.sonyericsson.extras.liveware-5.7.11.130.apk', 'com.soundcloud.android-14.10.01-27.apk',
#                 'com.sundaytoz.mobile.anipang2.google.kakao.service-1.0.35.apk', 'com.touchtype.swiftkey-5.0.5.95.apk',
#                 'com.utorrent.client-2.20.apk', 'com.venticake.retrica-2.2.3.apk', 'com.viber.voip-5.0.2.12.apk', 'com.whatsapp-2.11.399.apk',
#                 'com.wooga.diamonddash-3.4.apk', 'com.yahoo.mobile.client.android.mail-4.6.2.apk', 'com.zeptolab.ctr.ads-2.4.4.apk',
#                 'com.zynga.FarmVille2CountryEscape-2.1.127.apk', 'de.lotum.whatsinthefoto.us-4.2.apk', 'es.socialpoint.DragonCity-2.11.apk',
#                 'eu.nordeus.topeleven.android-2.32.1.apk', 'jp.naver.SJLGPP-2.1.4.apk', 'jp.naver.linecamera.android-8.6.3.apk',
#                 'logos.quiz.companies.game-16.2.apk', 'me.pou.app-1.4.61.apk', 'mobi.mgeek.TunnyBrowser-11.2.6.apk',
#                 'net.mobilecraft.realbasketball-1.8.apk', 'tunein.player-12.8.apk', 'vStudio.Android.Camera360-5.4.5.apk',
#                 'com.fdgentertainment.paperama-1.3.6.apk', 'com.king.candycrushsaga-1.39.4.apk', 'com.whatsapp.wallpaper-2.apk',
#                 'com.threed.bowling-2.6.apk', 'com.blurb.checkout-1.0.apk', 'com.lookout-9.6.4-f3c9c32.apk',
#                 'goldenshorestechnologies.brightestflashlight.free-2.4.2.apk', 'com.google.android.marvin.talkback-3.1.1_r68.apk',
#                 'com.julian.fastracing-1.1.apk', 'com.dsi.ant.plugins.antplus-3.1.0.apk', 'com.melimots.WordSearch-1.14.apk',
#                 'com.google.android.videos-2.0.21.apk', 'com.outfit7.talkingpierrefree-3.1.apk', 'Music2.apk',
#                 'com.yahoo.mobile.client.android.im-1.8.8.apk', 'flipboard.app-1.9.6.apk', 'com.fdgentertainment.bananakong-1.8.apk',
#                 'com.opera.mini.android-7.6.1.apk', 'Velvet.apk', 'com.linktomorrow.windrunner-3.82.apk', 'com.sec.android.fwupgrade-1.2.3717.apk',
#                 'com.game.SkaterBoy-1.6.apk', 'com.fingersoft.hillclimb-1.18.0.apk', 'com.ogqcorp.bgh-3.6.4.apk',
#                 'com.opera.browser-25.0.1619.84037.apk', 'com.linecorp.LGCOOKIE-2.0.5.apk', 'com.zeptolab.ctr2.f2p.google-1.1.7.apk',
#                 'com.kfactormedia.mycalendarmobile-3.02.apk', 'net.mobigame.zombietsunami-1.6.46.apk', 'com.dhqsolutions.enjoyphoto-2.0.0.apk',
#                 'com.google.zxing.client.android-4.7.0.apk', 'com.nekki.vector-1.1.0.apk', 'GoogleTTS.apk', 'com.google.android.street-1.8.1.2.apk',
#                 'Street.apk', 'com.rechild.advancedtaskkiller-2.0.3B203.apk', 'LatinImeGoogle.apk', 'com.adobe.reader-11.7.0.apk',
#                 'com.dsi.ant.service.socket-4.7.0.apk', 'com.sec.spp.push-1.2.9.1.apk', 'com.socialnmobile.dictapps.notepad.color.note-3.9.60.apk',
#                 'com.dropbox.android-2.1.11.apk', 'com.easy.battery.saver-3.4.1.apk', 'com.sec.pcw-1.0.1943.apk', 'com.umonistudio.tile-2.9.5.apk',
#                 'com.imangi.templerun-1.0.8.apk', 'com.google.android.apps.translate-3.0.15.apk', 'PlusOne.apk', 'com.estoty.game2048-6.22.apk',
#                 'com.devexpert.weather-4.1.1.apk', 'com.natenai.glowhockey-1.2.16.apk', 'com.duolingo-2.9.0.apk',
#                 'com.imdb.mobile-5.0.3.105030410.apk', 'com.NextFloor.DragonFlightKakao-2.6.2.apk', 'com.disney.WMWLite-1.9.1.apk',
#                 'com.bigduckgames.flow-2.8.apk']

to_test_list = ["com.sec.spp.push-1.apk"]


def parse_args():
    parser = argparse.ArgumentParser(description='RiteMobile Android melt test.')
    parser.add_argument('-b', '--build', required=False, action='store_true',
                        help="Rebuild apk")
    parser.add_argument('-i', '--interactive', required=False, action='store_true',
                        help="Interactive execution")
    parser.add_argument('-f', '--fastnet', required=False, action='store_true',
                        help="Install fastnet")
    parser.add_argument('-r', '--reboot', required=False, action='store_true',
                        help="Install fastnet")

    args = parser.parse_args()

    return args


def main():
    # from AVCommon import logger
    # logger.init()

    print "##### STARTING MELT ANDROID TEST #####"
    print "REMEMBER TO:"
    print "CONFIGURE: AV, BLACKLIST, WHITELIST"
    print "CONNECT A DEVICE"
    print "MOUNT THE SHARE"
    print "SAVE PREVIOUS LOGS"

    args = parse_args()

    command_dev = CommandsDevice()
    device_id = command_dev.get_dev_deviceid()

    # THIS SECTION BUILDS WITH MELT APK IN ZIPS AND STORE THEM INTO BUILD_MELT_DIR
    if "melt_server" in test_to_run:
        results = collections.OrderedDict()

        result_strings_all = []
        result_strings_ok = []
        result_strings_error = []

        fileok = open(os.path.join(build_melt_dir, "melt_ok.txt"), 'w')
        fileerror = open(os.path.join(build_melt_dir, "melt_error.txt"), 'w')

        try:
            if server == "castore":
                commands_rcs = CommandsRCSCastore(login_id=0, device_id=device_id)
            elif server == "polluce":
                commands_rcs = CommandsRCSPolluce(login_id=0, device_id=device_id)
            else:
                return
            with commands_rcs as c:
                unordered_list = os.listdir(apk_share_dir)[:max_test_iterations]
                shuffle(unordered_list)
                for apk_file in unordered_list:
                    # quelli da testare, ma che non sia gia' noto che funzionano o non che funzionano
                    if apk_file.endswith(".apk") and apk_file.startswith(filter_string) and not glob.glob(build_melt_dir+"melt_"+apk_file+".zip"):  # and os.path.basename(apk_file) in to_test_list:
                            # and os.path.basename(apk_file) not in these_works_list and os.path.basename(apk_file) not in these_does_not_work_list:
                        is_an_antivirus = False
                        installation_result = "UNKNOWN"
                        for avname in av_list:
                            if apk_file.startswith(avname):
                                is_an_antivirus = True
                        if is_an_antivirus:
                            installation_result = "ANTIVIRUS"
                            result_strings_error.append("%s:\t [ ANTIVIRUS ]" % apk_file)
                            fileerror.write("%s:\t [ ANTIVIRUS ]\n" % apk_file)
                            fileerror.flush()
                            os.fsync(fileerror.fileno())
                        else:
                            time.sleep(10)
                            repeat = 0
                            completed_test = False
                            while repeat <= max_timeout_retries and completed_test is False:
                                repeat += 1
                                try:

                                    #ret = c.build_melt_apk(melt_file=os.path.join(apk_share_dir, apk_file), appname="melted_%s" % apk_file,
                                          # melt_dir=build_melt_dir, ruby_build_in_second_stage=True)
                                    input_melt_file = os.path.join(apk_share_dir, apk_file)
                                    zipfilenamebackend = os.path.join(build_melt_dir, "melt_%s.zip" % apk_file)

                                    ret = c.build_melt_apk_ruby(input_melt_file, zipfilenamebackend=zipfilenamebackend, factory_id=commands_rcs.factory)
                                    if not ret:
                                        raise Exception("Build failed")
                                    installation_result = "Ok"
                                    result_strings_ok.append(apk_file)
                                    fileok.write("%s:\t [ Ok ]\n" % apk_file)
                                    fileok.flush()
                                    os.fsync(fileok.fileno())
                                    completed_test = True
                                except HTTPError as err:
                                    installation_result = "ERROR"
                                    result_strings_error.append("%s:\t [ ERROR ]" % apk_file)
                                    fileerror.write("%s:\t [ ERROR ]\n" % apk_file)
                                    fileerror.flush()
                                    os.fsync(fileerror.fileno())
                                    completed_test = True
                                except:
                                    time.sleep(10)
                                    print "%s:\t [ RETRY! (have tried %s times of %s max) ]" % (apk_file, repeat, max_timeout_retries+1)
                                    installation_result = "RETRIES EXCEEDED"
                                    result_strings_error.append("%s:\t [ RETRIES EXCEEDED ]" % apk_file)

                        result_string = "Result for %s: \t\t [ %s ]" % (apk_file, installation_result)
                        result_strings_all.append(result_string)
                        print result_string

        except Exception, ex:
            print ex
            traceback.print_exc()
            results['exception'] = ex

        finally:
            print "#######   ALL RESULTS   #######"
            for line in result_strings_all:
                print line

            fileok.close()
            fileerror.close()

    sync_ok = ['melt_melted_air.au.com.metro.DumbWaysToDie-1.6.apk.zip', 'melt_melted_ch.smalltech.ledflashlight.free-1.68.apk.zip',
               'melt_melted_com.accuweather.android-3.3.2.7.apk.zip', 'melt_melted_com.adobe.reader-11.7.0.apk.zip',
               'melt_melted_com.ansangha.drdriving-1.38.apk.zip', 'melt_melted_com.avast.android.mobilesecurity-3.0.7864.apk.zip',
               'melt_melted_com.amazon.mp3-4.1.1.apk.zip']

    # THIST PART GETS ZIPS FROM "build_melt_dir", INSTALLS, RUNS AND CHECK SYNC OF THEM
    if "zip_run" in test_to_run:

        if server == "castore":
            commands_rcs = CommandsRCSCastore(login_id=0, device_id=device_id)
        elif server == "polluce":
            commands_rcs = CommandsRCSPolluce(login_id=0, device_id=device_id)
        else:
            return
        print "Connected"

        fileinstallok = open(os.path.join(build_melt_dir, "install_ok.txt"), 'w')

        # command_dev.wifi("av", check_connection=True, install=True)
        with commands_rcs as c:
            ziplist = [filez for filez in os.listdir(build_melt_dir) if filez.endswith(".zip")]
            for zip_file_ok in ziplist[:max_test_iterations]:
                if zip_file_ok.startswith("melt_melted_"+filter_string) and zip_file_ok not in sync_ok:
                    print "+++=== PROCESSING %s ===+++" % zip_file_ok
                    zip_file_ok = os.path.join(build_melt_dir, zip_file_ok)
                    try:
                        c.delete_old_instance()
                        command_dev.clean_logcat()
                        installation_result = command_dev.install_zip(zip_file_ok)
                        if not installation_result:
                            addresult("%s:\t [ ERROR INSTALLATION FAILED ]" % zip_file_ok)
                            continue
                        else:
                            addresult("%s:\t [ INSTALLED ]" % zip_file_ok)
                            # print installation_result
                            package_name = androguardutils.get_package_from_apk(installation_result)
                            addresult("%s:\t [ GOT PACKAGENAME FROM ANDROGUARD ]" % package_name)
                            if not command_dev.launch_default_activity_monkey(package_name):
                                addresult("%s:\t [ ERROR FAILED MONKEY EXECUTION ]" % package_name)
                                continue
                            else:
                                addresult("%s:\t [ EXECUTED ]" % package_name)
                                command_dev.lock_and_unlock_screen()
                                time.sleep(30)
                                # if command_dev.is_agent_running():
                                #     addresult("%s:\t [ AGENT RUNNING ]" % package_name)
                                # else:
                                #     addresult("%s:\t [ ERROR AGENT NOT RUNNNING ]" % package_name)

                                if not command_dev.is_package_runnning(package_name):
                                    addresult("%s:\t [ ERROR APP NOT RUNNNING ]" % package_name)
                                    continue
                                else:
                                    addresult("%s:\t [ APP RUNNING ]" % package_name)
                                    addresult("%s:\t [ Now I try to fetch evidences ]" % package_name)
                                    c.wait_for_sync(command_dev.lock_and_unlock_screen())
                                    ev = c.evidences()
                                    if ev:
                                        addresult("%s:\t [ GOT EVIDENCES - SUCCESS!!! ]" % zip_file_ok)
                                        fileinstallok.write("%s < %s >\n" % (zip_file_ok, package_name))
                                        fileinstallok.flush()
                                        os.fsync(fileinstallok.fileno())
                                    else:
                                        addresult("%s:\t [ NO EVIDENCES - FAILED!!! ]" % package_name)
                                        continue


                    except Exception, ex:
                        addresult("%s:\t [ GENERIC ERROR ]" % zip_file_ok)
                        print ex
                        traceback.print_exc()
                    finally:
                        if not package_name:
                            addresult("%s:\t [ ERROR UNINSTALLING PACKAGE - ABORTING ]" % zip_file_ok)
                            return  # aborts test because cannot uninstall package
                        if uninstall:
                            command_dev.uninstall_package(package_name)
                        command_dev.save_logcat(zip_file_ok + "_logcat.txt")
                        addresult("%s:\t [ PACKAGE UNINSTALLED ]" % package_name)

            fileinstallok.close()
            time.sleep(2)
            print "#######   ALL RESULTS   #######"
            for line in result_installation:
                print line


def addresult(result):
    print result
    result_installation.append(result)


if __name__ == "__main__":
    main()
