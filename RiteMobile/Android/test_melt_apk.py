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

zenos_apk = ['ChatON_MARKET.apk', 'FWUpgrade.apk', 'GMS_Maps.apk', 'GroupPlay_25_stub.apk', 'SamsungLink18_stub.apk', 'Street.apk', 'VoiceSearchStub.apk', 'air.MSPMobile-1.apk', 'air.au.com.metro.DumbWaysToDie-1.apk', 'air.au.com.metro.DumbWaysToDie2-1.apk', 'air.com.elextech.happyfarm-1.apk', 'air.com.mobigrow.canyouescape-1.apk', 'air.com.playtika.slotomania-1.apk', 'air.com.sgn.cookiejam.gp-1.apk', 'air.com.ubisoft.csi.HiddenCrimes-1.apk', 'cn.jingling.motu.photowonder-1.apk', 'co.vine.android-1.apk', 'com.NextFloor.DragonFlightKakao-1.apk', 'com.StudioOnMars.CSPortable-1.apk', 'com.UCMobile.intl-1.apk', 'com.accuweather.android-1.apk', 'com.aceviral.angrygranrun-1.apk', 'com.activision.callofduty.heroes-1.apk', 'com.adobe.air-1.apk', 'com.adobe.reader-1.apk', 'com.alarmclock.xtreme.free-1.apk', 'com.ansangha.drdriving-1.apk', 'com.antivirus-1.apk', 'com.appstar.callrecorder-1.apk', 'com.apusapps.tools.booster-1.apk', 'com.apusapps.tools.unreadtips-1.apk', 'com.arcsoft.perfect365-1.apk', 'com.auxbrain.zombie_highway-1.apk', 'com.avast.android.mobilesecurity-1.apk', 'com.aws.android-1.apk', 'com.baidu.browser.inter-1.apk', 'com.baileyz.aquarium-1.apk', 'com.bbm-1.apk', 'com.bestcoolfungames.antsmasher-1.apk', 'com.bfs.papertoss-1.apk', 'com.bigduckgames.flow-1.apk', 'com.bitstrips.bitstrips-1.apk', 'com.blurb.checkout-1.apk', 'com.bsb.hike-1.apk', 'com.candyrufusgames.survivalcrafttrial-1.apk', 'com.cg.tennis-1.apk', 'com.ciegames.RacingRivals-1.apk', 'com.cleanmaster.mguard-1.apk', 'com.com2us.acefishing.normal.freefull.google.global.android.common-1.apk', 'com.com2us.smon.normal.freefull.google.kr.android.common-1.apk', 'com.creativemobile.DragRacing-1.apk', 'com.dataviz.docstogo-1.apk', 'com.dhqsolutions.enjoyphoto-1.apk', 'com.dianxinos.dxbs-1.apk', 'com.dianxinos.optimizer.duplay-1.apk', 'com.dictionary-1.apk', 'com.digidust.elokence.akinator.freemium-1.apk', 'com.digiplex.game-1.apk', 'com.disney.wheresmywater2_goo-1.apk', 'com.djinnworks.StickmanSoccer2014-1.apk', 'com.dragonplay.liveholdempro-1.apk', 'com.droidhen.game.racingmoto-1.apk', 'com.dsi.ant.plugins.antplus-1.apk', 'com.dsi.ant.service.socket-1.apk', 'com.ea.games.simsfreeplay_row-1.apk', 'com.estoty.game2048-1.apk', 'com.explorationbase.ExplorationLite-1.apk', 'com.fdgentertainment.bananakong-1.apk', 'com.fdgentertainment.paperama-1.apk', 'com.fingersoft.benjibananas-1.apk', 'com.fingersoft.hillclimb-1.apk', 'com.firsttouchgames.score-1.apk', 'com.flipkart.android-1.apk', 'com.forshared-1.apk', 'com.forshared.music-1.apk', 'com.forthblue.pool-1.apk', 'com.fungamesforfree.snipershooter.free-1.apk', 'com.futurebits.instamessage.free-1.apk', 'com.game.BMX_Boy-1.apk', 'com.game.JewelsStar-1.apk', 'com.game.SkaterBoy-1.apk', 'com.game.basketballshoot-1.apk', 'com.gamebasics.osm-1.apk', 'com.gameloft.android.ANMP.GloftCAHM-1.apk', 'com.gameloft.android.ANMP.GloftDMHM-1.apk', 'com.gameloft.android.ANMP.GloftIAHM-1.apk', 'com.gameloft.android.ANMP.GloftIVHM-1.apk', 'com.gameloft.android.ANMP.GloftJDHM-1.apk', 'com.gameloft.android.ANMP.GloftMTHM-1.apk', 'com.gameloft.android.ANMP.GloftPEHM-1.apk', 'com.gameloft.android.ANMP.GloftPOHM-1.apk', 'com.gameloft.android.ANMP.GloftSIHM-1.apk', 'com.gamevil.cartoonwars.one.global-1.apk', 'com.gamevil.kritikamobile.android.google.global.normal-1.apk', 'com.gamevil.punchhero.glo-1.apk', 'com.gau.go.launcherex-1.apk', 'com.genina.android.blackjack.view-1.apk', 'com.google.zxing.client.android-1.apk', 'com.hbwares.wordfeud.free-1.apk', 'com.herman.ringtone-1.apk', 'com.hotdog.tinybattle-1.apk', 'com.ijinshan.kbatterydoctor_en-1.apk', 'com.imangi.templerun-1.apk', 'com.imangi.templerun2-1.apk', 'com.incredibleapp.wallpapershd-1.apk', 'com.instagram.android-1.apk', 'com.intellectualflame.ledflashlight.washer-1.apk', 'com.jb.emoji.gokeyboard-1.apk', 'com.jb.gokeyboard-1.apk', 'com.jb.gosms-1.apk', 'com.jellybtn.cashkingmobile-1.apk', 'com.jiubang.goscreenlock-1.apk', 'com.julian.fastracing-1.apk', 'com.julian.motorboat-1.apk', 'com.ketchapp.stickhero-1.apk', 'com.ketchapp.zigzaggame-1.apk', 'com.kfactormedia.mycalendarmobile-1.apk', 'com.kiloo.subwaysurf-1.apk', 'com.king.candycrushsaga-1.apk', 'com.king.candycrushsodasaga-1.apk', 'com.king.farmheroessaga-1.apk', 'com.king.petrescuesaga-1.apk', 'com.king.pyramidsolitairesaga-1.apk', 'com.kiragames.unblockmefree-1.apk', 'com.kittyplay.ex-1.apk', 'com.kms.free-1.apk', 'com.leftover.CoinDozer-1.apk', 'com.lima.doodlejump-1.apk', 'com.linecorp.LGCOOKIE-1.apk', 'com.linecorp.LGRGS-1.apk', 'com.linecorp.b612.android-1.apk', 'com.linkedin.android-1.apk', 'com.linktomorrow.candypang-1.apk', 'com.linktomorrow.windrunner-1.apk', 'com.lookout-1.apk', 'com.ludia.dragons-1.apk', 'com.ludia.jurassicpark-1.apk', 'com.madhead.tos.zh-1.apk', 'com.magmamobile.game.BubbleBlast2-1.apk', 'com.magmamobile.game.Burger-1.apk', 'com.magmamobile.game.mousetrap-1.apk', 'com.manboker.headportrait-1.apk', 'com.mapfactor.navigator-1.apk', 'com.mediocre.smashhit-1.apk', 'com.melimots.WordSearch-1.apk', 'com.miantan.myoface-1.apk', 'com.midasplayer.apps.bubblewitchsaga2-1.apk', 'com.midasplayer.apps.diamonddiggersaga-1.apk', 'com.midasplayer.apps.papapearsaga-1.apk', 'com.miniclip.eightballpool-1.apk', 'com.miniclip.plagueinc-1.apk', 'com.miniclip.railrush-1.apk', 'com.mobage.ww.a5225.tf2_Android-1.apk', 'com.mobilityware.solitaire-1.apk', 'com.moistrue.zombiesmasher-1.apk', 'com.myfitnesspal.android-1.apk', 'com.natenai.glowhockey-1.apk', 'com.nekki.vector-1.apk', 'com.nhn.android.search-1.apk', 'com.nordcurrent.Games101-1.apk', 'com.octro.teenpatti-1.apk', 'com.ogqcorp.bgh-1.apk', 'com.oovoo-1.apk', 'com.opera.browser-1.apk', 'com.outfit7.gingersbirthdayfree-1.apk', 'com.outfit7.jigtyfree-1.apk', 'com.outfit7.movingeye.swampattack-1.apk', 'com.outfit7.talkingangelafree-1.apk', 'com.outfit7.talkingben-1.apk', 'com.outfit7.talkinggingerfree-1.apk', 'com.outfit7.talkingnewsfree-1.apk', 'com.outfit7.talkingpierrefree-1.apk', 'com.outfit7.talkingtom2free-1.apk', 'com.outfit7.tomlovesangelafree-1.apk', 'com.outfit7.tomslovelettersfree-1.apk', 'com.outlook.Z7-1.apk', 'com.pixlr.express-1.apk', 'com.pof.android-1.apk', 'com.polarbit.rthunder2lite-1.apk', 'com.policydm-1.apk', 'com.popularapp.periodcalendar-1.apk', 'com.progrestar.bft-1.apk', 'com.qihoo.security-1.apk', 'com.quvideo.xiaoying-1.apk', 'com.rechild.advancedtaskkiller-1.apk', 'com.robtopx.geometryjumplite-1.apk', 'com.roidapp.photogrid-1.apk', 'com.rovio.angrybirds-1.apk', 'com.rovio.angrybirdsfriends-1.apk', 'com.rovio.angrybirdsspace.ads-1.apk', 'com.rovio.angrybirdsstarwars.ads.iap-1.apk', 'com.rovio.angrybirdsstarwarsii.ads-1.apk', 'com.rovio.angrybirdsstella-1.apk', 'com.scottgames.fnaf2demo-1.apk', 'com.seriouscorp.clumsybird-1.apk', 'com.seventeenbullets.android.island-1.apk', 'com.sgiggle.production-1.apk', 'com.shootbubble.bubbledexlue-1.apk', 'com.sidheinteractive.sif.DR-1.apk', 'com.skout.android-1.apk', 'com.skype.raider-1.apk', 'com.smule.magicpiano-1.apk', 'com.snkplaymore.android003-1.apk', 'com.socialnmobile.dictapps.notepad.color.note-1.apk', 'com.socialquantum.acityint-1.apk', 'com.sp.protector.free-1.apk', 'com.springwalk.mediaconverter-1.apk', 'com.stac.empire.main-1.apk', 'com.sundaytoz.mobile.anipang2.google.kakao.service-1.apk', 'com.surpax.ledflashlight.panel-1.apk', 'com.sydneyapps.remotecontrol-1.apk', 'com.sygic.aura-1.apk', 'com.symantec.mobilesecurity-1.apk', 'com.theonegames.gunshipbattle-1.apk', 'com.threed.bowling-1.apk', 'com.topfreegames.bikeracefreeworld-1.apk', 'com.touchtype.swiftkey-1.apk', 'com.tripadvisor.tripadvisor-1.apk', 'com.uc.browser.en-1.apk', 'com.umonistudio.tile-1.apk', 'com.utorrent.client-1.apk', 'com.viber.voip-1.apk', 'com.wantu.activity-1.apk', 'com.weather.Weather-1.apk', 'com.whatsapp-1.apk', 'com.whatsapp.wallpaper-1.apk', 'com.wooga.jelly_splash-1.apk', 'com.wordsmobile.zombieroadkill-1.apk', 'com.xs.armysniper-1.apk', 'com.yahoo.mobile.client.android.im-1.apk', 'com.yahoo.mobile.client.android.mail-1.apk', 'com.yahoo.mobile.client.android.weather-1.apk', 'com.zentertain.photocollage-1.apk', 'com.zentertain.photoeditor-1.apk', 'com.zeptolab.ctr.ads-1.apk', 'com.zeptolab.ctr2.f2p.google-1.apk', 'com.zeptolab.timetravel.free.google-1.apk', 'com.zeroteam.zerolauncher-1.apk', 'com.zynga.livepoker-1.apk', 'com.zynga.looney-1.apk', 'com.zynga.scramble-1.apk', 'com.zynga.words-1.apk', 'de.lotum.whatsinthefoto.es-1.apk', 'de.lotum.whatsinthefoto.us-1.apk', 'es.socialpoint.MonsterLegends-1.apk', 'eu.nordeus.topeleven.android-1.apk', 'goldenshorestechnologies.brightestflashlight.free-1.apk', 'hotspotshield.android.vpn-1.apk', 'jp.naver.SJLGPP-1.apk', 'jp.naver.SJLGWR-1.apk', 'kik.android-1.apk', 'logos.quiz.companies.game-1.apk', 'me.pou.app-1.apk', 'mobi.mgeek.TunnyBrowser-1.apk', 'net.mobigame.zombietsunami-1.apk', 'net.mobilecraft.realbasketball-1.apk', 'net.one97.paytm-1.apk', 'net.wargaming.wot.blitz-1.apk', 'net.zedge.android-1.apk', 'org.zwanoo.android.speedtest-1.apk', 'ru.mail.games.android.JungleHeat-1.apk', 'tv.twitch.android.viewer-1.apk', 'uk.co.aifactory.chessfree-1.apk', 'vStudio.Android.Camera360-1.apk', 'wp.wattpad-1.apk']


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
                while True:
                    unordered_list = os.listdir(apk_share_dir)[:max_test_iterations]
                    shuffle(unordered_list)
                    for apk_file in unordered_list:
                        print apk_file
                        # quelli da testare, ma che non sia gia' noto che funzionano o non che funzionano
                        if apk_file.endswith(".apk") and apk_file.startswith(filter_string) and not glob.glob(build_melt_dir+"melt_"+apk_file+".zip")\
                                and apk_file in zenos_apk:  # and os.path.basename(apk_file) in to_test_list:
                                # and os.path.basename(apk_file) not in these_works_list and os.path.basename(apk_file) not in these_does_not_work_list:
                            print "Starting"
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
                        else:
                            print "skipping " + apk_file
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
