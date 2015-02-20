__author__ = 'mlosito'

import mimetypes
import urllib2
import mimetools
import os


#use just ip for host (default = Rit# e)
def post_image(to_post_file_name, host="172.20.20.192", av=None):

    dest = "http://%s:55002/" % host

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
    post_string += '' + '\r\n'
    post_string += payload + '\r\n'
    post_string += '--' + bound + '--\r\n'

    request = urllib2.Request(dest)
    # request.add_header('User-agent', 'PyMOTW (http://www.doughellmann.com/PyMOTW/)')
    body = post_string
    request.add_header('Content-type', 'multipart/form-data; boundary=%s' % bound)
    request.add_header('Content-length', len(body))
    request.add_data(body)

    #debug
    print request.get_data()

    resp = urllib2.urlopen(request).read()

    print resp
    return resp


def parse_response(resp):
    resu = resp.splitlines()[0]
    resu = resu.replace("Result= ", "").strip()

    filename = resp.splitlines()[1]
    filename = filename.replace("Thumb= ", "").strip()

    if resu in ["NO_TEXT", "GOOD", "BAD", "CRASH", "UNKNOWN"]:
        return resu, filename
    else:
        return False

if __name__ == "__main__":
    resp = post_image("/Users/mlosito/Desktop/241.png", host="172.20.20.192", av="avira")
    resu, thumb_filename = parse_response(resp)
    print resu
    print thumb_filename
