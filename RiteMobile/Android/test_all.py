
import test_functional_persistence as pers
import test_functional_photo as photo
import test_functional_audio as audio
import test_functional_chat as chat

from test_all_specific import AllTestSpecific

import functional_common

from RiteMobile.Android.commands_rcs import CommandsRCSCastore as CommandsRCS

if __name__ == '__main__':
    test_pers = pers.PersistenceTestSpecific()
    test_photo = photo.PhotoTestSpecific()
    test_audio = audio.AudioTestSpecific()
    test_chat = chat.ChatTestSpecific()

    results = functional_common.test_functional_all([ test_pers, test_photo,test_audio, test_chat  ], CommandsRCS)