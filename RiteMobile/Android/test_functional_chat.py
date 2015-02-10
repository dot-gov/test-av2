from collections import Counter
from sets import Set
import functional_common
import sys
import time


class ChatTestSpecific(functional_common.Check):

    def get_name(self):
        return "chat"

    def get_chat_packages(self, command_dev):
        chat = set()
        packs = []
        addressbook = []
        addressbooks = ['skype', 'facebook', 'wechat', 'google']
        conversion={
            'tencent.mm':'facebook', 'android.talk':'google', 'line.android':'line'
        }
        packages = command_dev.get_packages()
        for i in ['skype', 'facebook', 'wechat', 'telegram', 'hangout', 'android.talk', 'line.android', 'viber',
                  'tencent.mm', 'whatsapp']:
            for p in packages:
                if i in p:
                    converted =  conversion.get(i,i)
                    chat.add( converted )
                    if converted in addressbooks:
                        addressbook.append(converted)
                    packs.append(p)

        return chat, addressbook, packs

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
        expected, addressbook, packs = self.get_chat_packages(command_dev)
        results['expected_chat'] = expected
        results['expected_addressbook'] = addressbook

        if results['have_root']:
            # check chat
            print "CHAT"
            #self.check_chat(command_dev, packs)

    def check_ev_program(self, prog, expected):
        programs = results['evidence_programs_last'].get(prog, [])
        print "programs %s: " % prog, programs
        ret = True
        # expected: ['telegram', 'android.talk', 'viber', 'facebook', 'line.android', 'skype', 'whatsapp', 'tencent.mm']
        # Counter({u'whatsapp': 14, u'wechat': 9, u'skype': 7, u'viber': 6, u'telegram': 3, u'line': 3, u'facebook': 1})
        for e in expected:
            found = False
            for p in programs:
                if p in e:
                    found = True
                    break
            if not found:
                print "FAILED: " + e
                ret = False
        return ret

    def final_assertions(self, results):

        ret = self.check_ev_program('chat', results.get('expected_chat',[]))
        ret &= self.check_ev_program('addressbook', results.get('expected_addressbook',[]))

        return ret


from RiteMobile.Android.commands_rcs import CommandsRCSCastore as CommandsRCS


if __name__ == '__main__':
    test_photo = ChatTestSpecific()
    results = functional_common.test_functional_common(test_photo, CommandsRCS)