import functional_common
import sys
import time


class AudioTestSpecific(functional_common.TestFunctionalBase):

    def get_name(self):
        return "audio"

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

        results['expected'].append('skype')
        print "waiting for call inject"
        info_evidences = []
        counter = 0
        while not info_evidences and counter < 10:
            info_evidences = c.infos('Call')

            counter += 1
            if not info_evidences:
                print "waiting for info"
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
        command_dev.execute_cmd("am start com.android.contacts")
        time.sleep(30)
        # if command_dev.check_remote_process("com.android.contacts", 5) == -1:
        #     if command_dev.check_remote_process("ResolverActivity", 5) == -1:
        #         command_dev.press_key_enter()
        #     if command_dev.check_remote_process("com.android.contacts", 5) == -1:
        #         if command_dev.check_remote_process("ResolverActivity", 5) != -1:
        #             command_dev.press_key_enter()
        #             command_dev.press_key_enter()
        #             command_dev.press_key_tab()
        #             command_dev.press_key_tab()
        #             command_dev.press_key_enter()
        info_evidences = []
        counter = 0
        while not self.check_evidences_present(commands_rcs, "mic") and counter < 10:
            counter += 1
            if not info_evidences:
                print "waiting for mic evidence"
                time.sleep(10)
            else:
                break
        command_dev.press_key_home()


    def test_device(self, args, command_dev, c, results):

        results['expected'] = []
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
        programs = results['evidence_programs_last'].get('call',[])

        ret = True
        info = ""
        # expected: ['telegram', 'android.talk', 'viber', 'facebook', 'line.android', 'skype', 'whatsapp', 'tencent.mm']
        # Counter({u'whatsapp': 14, u'wechat': 9, u'skype': 7, u'viber': 6, u'telegram': 3, u'line': 3, u'facebook': 1})
        for e in results['expected']:
            found = False
            for p in programs:
                if p in e:
                    found = True
                    break
            if not found:
                info+= "\t\t\tFAILED: " + e + "\n"
                ret = False

        for t in ['mic']:
            if t not in results['evidence_types_last']:
                info+= "\t\t\tFAILED: " + t + "\n"
                ret = False

        if results['have_root']:
            for t in ['call','camera']:
                if t not in results['evidence_types_last']:
                    info+= "\t\t\tFAILED: " + t + "\n"
                    ret = False

        return ret, info


from RiteMobile.Android.commands_rcs import CommandsRCSCastore as CommandsRCS


if __name__ == '__main__':
    test_photo = AudioTestSpecific()
    results = functional_common.test_functional_common(test_photo, CommandsRCS)