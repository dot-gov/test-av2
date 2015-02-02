import functional_common
import sys
import time


class TestSpecific(functional_common.Check):
    def get_config(self):
        return open('assets/config_mobile_chat.json').read()

    def get_chat_packages(self, command_dev):
        chat = set()
        packs = []
        packages = command_dev.get_packages()
        for i in ['skype', 'facebook', 'wechat', 'telegram', 'hangout', 'android.talk', 'line.android', 'viber',
                  'tencent.mm', 'whatsapp']:
            for p in packages:
                if i in p:
                    chat.add(i)
                    packs.append(p)
        return chat, packs

    def check_chat(self, command_dev):
        command_dev.press_key_home()
        expected, chats = self.get_chat_packages(command_dev)
        for c in chats:
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
        results['expected'] = list(expected)
        self.check_evidences(command_dev, c, results, "_first")

        if results['have_root']:
            # check chat
            print "CHAT"
            self.check_chat(command_dev)

    def final_assertions(self, results):
        return True


from RiteMobile.Android.commands_rcs import CommandsRCSCastore as CommandsRCS


if __name__ == '__main__':
    test_photo = TestSpecific()
    results = functional_common.test_functional_common(test_photo, CommandsRCS)