from collections import Counter
from sets import Set
import functional_common
import sys
import time

from specific_test_functional_base import SpecificTestFunctionalBase
class ChatTestSpecific(SpecificTestFunctionalBase):

    def get_info(self):
        return """ Enables ADDRESSBOOK, CHAT and check that:
         - Addressbook are saved
         - Chats are saved
        """

    def get_name(self):
        return "chat"

    def get_chat_packages(self, command_dev):
        chat = set()
        packs = []
        addressbook = []
        addressbooks = ['skype', 'facebook', 'gmail']
        conversion={
            'tencent.mm':'facebook', 'line.android':'line'
        }
        packages = command_dev.get_packages()

        no_more_supported= ['tencent.mm',]
        for i in ['skype', 'facebook', 'wechat', 'telegram', 'hangout', 'line.android', 'viber',
                  'whatsapp']:
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
            if args.interactive:
                self.check_chat(command_dev, packs)

    def check_ev_program(self, results, prog, expected):
        programs = results['evidence_programs_last'].get(prog, [])
        print "programs %s: " % prog, programs
        ret = True
        info = ""
        # expected: ['telegram', 'android.talk', 'viber', 'facebook', 'line.android', 'skype', 'whatsapp', 'tencent.mm']
        # Counter({u'whatsapp': 14, u'wechat': 9, u'skype': 7, u'viber': 6, u'telegram': 3, u'line': 3, u'facebook': 1})
        for e in expected:
            found = False
            for p in programs:
                if p in e:
                    found = True
                    break
            if not found:
                info+= "\t\t\tFAILED: " + e + "\n"
                ret = False
        return ret, info

    def final_assertions(self, results):
        info = ""
        if not results['have_root']:
            info = "\t\t\tFAILED: no ROOT\n"
            return False, info

        ret1, info1 = self.check_ev_program(results, 'chat',  results.get('expected_chat',[]))
        ret2, info2= self.check_ev_program(results, 'addressbook', results.get('expected_addressbook',[]))

        return ret1 and ret2, info1 + info2


from RiteMobile.Android.commands_rcs import CommandsRCSCastore as CommandsRCS


if __name__ == '__main__':
    test_photo = ChatTestSpecific()
    results = functional_common.test_functional_common(test_photo, CommandsRCS)