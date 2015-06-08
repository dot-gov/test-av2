import base64
from urllib2 import URLError

__author__ = 'mlosito'

import mimetypes
import urllib2
import mimetools
import os


#use just ip for host (default = Rit# e)
def post_image(to_post_file_name, host="10.0.20.1", av=None):

    dest = "http://%s:55002/" % host

    print(dest)

    to_post_file_handle = open(to_post_file_name, "rb")
    payload = to_post_file_handle.read()
    print("DBG payload size: %s file:  %s" % (len(payload), to_post_file_name))
    # melt_id = http_client._call_post('', payload, binary=True, argjson=False)

    mimetype = mimetypes.guess_type(to_post_file_name)[0] or 'application/octet-stream'

    bound = mimetools.choose_boundary()

    post_string = '--' + bound + '\r\n'

    if av:
        post_string += 'Content-Disposition: form-data; name="av"\r\n'
        post_string += '\r\n'
        post_string += av + '\r\n'
        post_string += '--' + bound + '\r\n'

    post_string += 'Content-Disposition: file; name="%s"; filename="%s" \r\n' % ('image', os.path.basename(to_post_file_name))
    post_string += 'Content-Type: %s \r\n' % mimetype
    post_string += "Content-transfer-encoding: base64 \r\n"
    post_string += '' + '\r\n'
    #UnicodeDecodeError
    #post_string += urllib2.quote(payload) + '\r\n'
    post_string += base64.b64encode(payload) + '\r\n'
    post_string += '--' + bound + '--\r\n'

    request = urllib2.Request(dest)
    # request.add_header('User-agent', 'PyMOTW (http://www.doughellmann.com/PyMOTW/)')
    body = post_string
    request.add_header('Content-type', 'multipart/form-data; boundary=%s' % bound)
    request.add_header('Content-length', len(body))
    request.add_data(body)

    print "POST Content-length: %s" % len(body)
    #debug
    #print request.get_data()
    try:
        resp = urllib2.urlopen(request).read()
    except URLError:
        return "ERROR - Impossible to contact host: tesserest server is up?"

    #print resp
    return resp


def parse_response(resp, server):
    if resp.startswith("ERROR - Impossible to contact host:"):
        return False, "SERVER_ERROR", "Impossible to contact host: %s" % server
    resu = resp.splitlines()[0]
    resu = resu.replace("Result= ", "").strip()

    filename = resp.splitlines()[1]
    filename = filename.replace("Thumb= ", "").strip()

    word = resp.splitlines()[2]
    word = word.replace("Found= ", "").strip()

    if resu in ["NO_TEXT", "GOOD", "BAD", "CRASH", "UNKNOWN"]:
        return resu, filename, word
    else:
        return False, None, ''

if __name__ == "__main__":
    resp = post_image("/Users/mlosito/Desktop/241.png", host="172.20.20.192", av="avira")
    # print resp
    resu, thumb_filename, word = parse_response(resp, "172.20.20.192")
    print resu
    print thumb_filename
    print word
