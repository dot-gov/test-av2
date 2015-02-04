from collections import Counter
from sets import Set
import functional_common
import sys
import time


class TestSpecific(functional_common.Check):
    def get_config(self):
        return open('assets/config_mobile_chat.json').read()

    def get_chat_packages(self, command_dev):
        chat = set()
        packs = []

        conversion={
            'tencent.mm':'facebook', 'android.talk':'google', 'line.android':'line'
        }
        packages = command_dev.get_packages()
        for i in ['skype', 'facebook', 'wechat', 'telegram', 'hangout', 'android.talk', 'line.android', 'viber',
                  'tencent.mm', 'whatsapp']:
            for p in packages:
                if i in p:
                    chat.add( conversion.get(i,i) )
                    packs.append(p)
        return chat, packs

    def check_chat(self, command_dev, packs):
        command_dev.press_key_home()

        for c in packs:
            print "Running chat: %s " % c

            command_dev.launch_default_activity_monkey(c)
            time.sleep(10)

            for i in range(10):
                print "wait..."
                time.sleep(5)
                if not command_dev.check_remote_activity(c, 1):
                    break

    def test_device(self, args, command_dev, c, results):
        expected, packs = self.get_chat_packages(command_dev)
        results['expected'] = expected

        if results['have_root']:
            # check chat
            print "CHAT"
            #self.check_chat(command_dev, packs)

    def final_assertions(self, results):
        evidences = results['evidences_details_last']
        programset =  Set([e['data']['program'] for e in evidences if e['type'] == "chat"])
        programs = list(programset)

        counter = Counter(programs)
        print counter

        ret = True
        # expected: ['telegram', 'android.talk', 'viber', 'facebook', 'line.android', 'skype', 'whatsapp', 'tencent.mm']
        # Counter({u'whatsapp': 14, u'wechat': 9, u'skype': 7, u'viber': 6, u'telegram': 3, u'line': 3, u'facebook': 1})
        for e in results['expected']:
            found = False
            for p in counter.keys():
                if p in e:
                    found = True
                    break
            if not found:
                print "FAILED: " + e
                ret = False
        return ret


from RiteMobile.Android.commands_rcs import CommandsRCSCastore as CommandsRCS


if __name__ == '__main__':
    test_photo = TestSpecific()
    results = functional_common.test_functional_common(test_photo, CommandsRCS)