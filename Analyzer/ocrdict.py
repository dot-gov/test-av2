__author__ = 'mlosito'

alphabet = 'abcdefghijklmnopqrstuvwxyz1234567890'


#Beware of three letter words! Prepend 'x'!

_good = {'performance', 'complete', 'Protection', 'enabled', 'LIVE', 'TECH', 'SUPPORT', 'Awake', 'ACTIVATE',
         'Mobile', 'Family', 'Safety', 'Update', 'UPDATE', 'FAILED', 'top-rated', 'tablet', 'Maxumize', 'maximiza',
         'free', 'trial', 'shopping', 'banking', 'watching', 'videos', 'Gamirg', 'surfirg', 'Protectior', 'actually', 'Surf', 'without',
         'interruptions', 'speeds', 'performance', 'complete', '24171365', 'LIVE', 'TECH', 'SUPPORT', 'databases', 'ugdatg', 'update', 'updating'}

_crash = {'stopped', 'working', 'solution', 'problem', 'time', 'online', 'solution', 'later', 'close'}

_bad = {'Block', 'blocked', 'nimocia', 'quarantena', 'Maggiori', 'Disinfezione', 'eininazione', 'Attendi', 'prooesso', 'Hilaccia', 'rievata',
       'minaccia', 'devata', 'quarantena', 'Maggiori', 'deltagi', 'Virus', 'removed', 'infected',
       'been', 'deleted', 'action', 'alert', 'THREAT', 'DELETED', 'default.apk', 'classes.dex', 'quarantena', 'Maggioi', 'maggiori',
       'Disinfezione', 'minaccia', 'rievata', 'eininazione.', 'Attendi', 'prooesso', 'Disinfezione', 'minaccia', 'rievata', 'rilevata',
       'eininazione', 'eliminazione', 'Attendi', 'termine', 'processo', 'prooesso', 'installdefaultapk', 'infected', 'handling', 'failed',
       'action', 'alert', 'Request', 'Outbound', 'Traffc', 'Detected', 'detected', 'large', 'amount', 'suspicious',
       'outbound', 'traffc', 'infected', 'something', 'Power', 'Eraser', 'detect', 'remove', 'Power', 'Eraser', 'message', 'outbound',
       'traffti', 'traffic', 'virus', 'W0rm', 'Kid0', 'install.exe', 'Malware', 'detected', 'MPRESS', 'HEUR', 'contains',
       'Trojan', 'IphcuneOS', 'Malware', 'detected', 'contains', 'Trojan', 'IphoneOS', 'Mekir', 'Accessing',
       'contains', 'Trojan', 'Malware', 'detected', 'Accessing', 'contains', 'Trojan', 'IOSinfect0r',
       'Accessing', 'contains', 'Trojan', 'IOSinfector', 'Deleted', 'Virus', 'removed', 'Betas', 'Threat',
       'found', 'Threat', 'variant', 'Win32', 'Boychi', 'cleaned', 'deleting', 'quarantined', 'vira', 'eliminazione',
       'MalwaelRisk',
        ' Spy', ' PID', 'worm ', 'Blackberry', 'Mekina'}
        # removed: 'program'  'detagi', 'dettagli', 'Details',

_badbad = {'Intel', 'lntel', 'Chipset', 'Utility', 'Backup', 'ChipUtil', 'SmartDefrag', 'DiskInfo', 'EditPad', 'TreeSizeFree', 'bkmaker', 'agent',
           'Crisis', 'Morkut', 'zrcs', 'hackingteam', 'hacking', 'CrystalDisklnfo', 'lntel(c)', 'Chipset', 'Utility'}

_ignore_list_av = {'Kaspersky', 'Internet', 'Security', '2013', 'COMODO', 'Norton', 'SMART', 'AVG', 'Bitdefender', 'avira',
                   'CMC'}
_ignore_list = {'AntiVirus'}

_white_white_list = {'First Computer Scan'}

class OcrDict():

    def __init__(self):
        self.white_white_list = {}
        self.good = {}
        self.crash = {}
        self.badall = {}

        self.size = 0

        #av not used yet
        for e in _white_white_list:
            perm = permutation(e.lower())
            self.white_white_list[e] = perm
            self.size += len(perm)
        for e in _good:
            perm = permutation(e.lower())
            self.good[e] = perm
            self.size += len(perm)
        for e in _crash:
            perm = permutation(e.lower())
            self.crash[e] = perm
            self.size += len(perm)
        for e in _bad:
            perm = permutation(e.lower())
            self.badall[e] = perm
            self.size += len(perm)
            perm = permutation(e.lower())
        for e in _badbad:
            self.badall[e] = perm
            self.size += len(perm)

        self.original_size = len(self.white_white_list) + len(self.good) + len(self.crash) + len(self.badall)

        # for e in _good:
        #     self.good.update(permutation(e.lower()))
        # for e in _crash:
        #     self.crash.update(permutation(e.lower()))
        # for e in _bad:
        #     self.badall.update(permutation(e.lower()))
        # for e in _badbad:
        #     self.badall.update(permutation(e.lower()))

    def parseresult(self, text):

        text = text.lower()

        text = remove_ignorelist(text)

        if not len(text.strip()):
            return "NO_TEXT", "", "", ""
        for k, v in self.white_white_list.items():
            for word in v:
                if word in text:
                    return "VGOOD", word, k, " - found: '%s' sounds like: '%s'" % (word, k)

        for k, v in self.badall.items():
            for word in v:
                if word in text:
                    return "BAD", word, k, " - found: '%s' sounds like: '%s'" % (word, k)

        for k, v in self.crash.items():
            for word in v:
                if word in text:
                    return "CRASH", word, k, " - found: '%s' sounds like: '%s'" % (word, k)

        for k, v in self.good.items():
            for word in v:
                if word in text:
                    return "GOOD", word, k, " - found: '%s' sounds like: '%s'" % (word, k)

        return "UNKNOWN", "", "", " - full text:\n%s" % text


def permutation(word):
    # every possibile split in word, not to be used
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    # removes a single letter
    deletes = [a + b[1:] for a, b in splits if b]
    # reverse letter order
    transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1]
    # replaces a letter
    replaces = [a + c + b[1:] for a, b in splits for c in alphabet if b]
    #insert a letter
    inserts = [a + c + b for a, b in splits for c in alphabet]

    return set(deletes + transposes + replaces + inserts)


def remove_ignorelist(text):
    for i in _ignore_list:
        text = text.replace(i.lower(), "")
    for i in _ignore_list_av:
        text = text.replace(i.lower(), "")

    return text