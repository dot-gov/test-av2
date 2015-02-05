import functional_common
import sys
import time


class TestSpecific(functional_common.Check):

    def get_config(self):
        return open('assets/config_mobile_chat.json').read()

    def check_evidences(self, command_dev, c, results, timestamp=""):
        print "... check_evidences"
        time.sleep(60)
        evidences, kinds = c.evidences()

        for k in ["call", "chat", "camera", "application", "mic"]:
            if k not in kinds.keys():
                kinds[k] = []

        ev = "\n"
        ok = kinds.keys()
        ok.sort()
        for k in ok:
            ev += "\t\t%s: %s\n" % (k, len(kinds[k]))
            if k in ["chat", "addressbook", "call"]:
                program = [e['data']['program'] for e in evidences if e['type'] == k]
                chat = set(program)
                for c in chat:
                    ev += "\t\t\t%s\n" % (c)

        results['evidences' + timestamp] = ev
        results['evidence_types' + timestamp] = kinds.keys()

        results['uptime' + timestamp] = command_dev.get_uptime()

        expected, packs = self.get_chat_packages(command_dev)
        results['expected'] = list(expected)


    def check_skype(self, command_dev, c, results):
        supported = ['4.0', '4.1', '4.2', '4.3']
        release = results['release'][0:3]

        results['call_supported'] = release in supported
        if release not in supported:
            print "Call not supported"
            return

        # check if skype is installed
        if command_dev.check_remote_app_installed("com.skype.raider", 5) != 1:
            print "skype not installed, skypping test"
            return

        print "... waiting for call inject"
        info_evidences = []
        counter = 0
        while not info_evidences and counter < 10:
            info_evidences = c.infos('Call')

            counter += 1
            if not info_evidences:
                print "... waiting for info"
                time.sleep(10)
            else:
                break

        for i in range(10):
            time.sleep(10)
            ret = command_dev.execute_root("ls /data/data/com.android.dvci/files/l4")
            print ret
            if "No such file" not in ret:
                print "Skype call and sleep"
                command_dev.skype_call()
                time.sleep(90)
                ret = command_dev.execute_root("ls /data/data/com.android.dvci/files/l4")
                print ret
                break


    def check_camera(self, command_dev):
        command_dev.press_key_home()
        command_dev.execute_camera()
        time.sleep(5)
        command_dev.press_key_home()


    def check_mic(self, command_dev, commands_rcs):
        command_dev.press_key_home()
        # on contacts start mic
        command_dev.execute_cmd(
            "am start com.android.contacts -n  com.android.contacts/.activities.DialtactsActivity -c android.intent.category.LAUNCHER")
        time.sleep(2)
        if command_dev.check_remote_process("com.android.contacts", 5) == -1:
            if command_dev.check_remote_process("ResolverActivity", 5) == -1:
                command_dev.press_key_enter()
            if command_dev.check_remote_process("com.android.contacts", 5) == -1:
                if command_dev.check_remote_process("ResolverActivity", 5) != -1:
                    command_dev.press_key_enter()
                    command_dev.press_key_enter()
                    command_dev.press_key_tab()
                    command_dev.press_key_tab()
                    command_dev.press_key_enter()
        info_evidences = []
        counter = 0
        while not self.check_evidences_present(commands_rcs, "mic") and counter < 10:
            counter += 1
            if not info_evidences:
                print "... waiting for mic evidence"
                time.sleep(10)
                if command_dev.isVersion(4, 0, -1) > 0:
                    command_dev.lock_and_unlock_screen()
                else:
                    command_dev.unlock()
            else:
                break
        command_dev.press_key_home()


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

        if results['have_root']:
            # skype call
            print "SKYPE"
            self.check_skype(command_dev, c, results)

            # check camera
            print "CAMERA"
            self.check_camera(command_dev)

            # check mic
            print "MIC"
            self.check_mic(command_dev, c)

    def final_assertions(self, results):
        return True


from RiteMobile.Android.commands_rcs import CommandsRCSCastore as CommandsRCS


if __name__ == '__main__':
    test_photo = TestSpecific()
    results = functional_common.test_functional_common(test_photo, CommandsRCS)