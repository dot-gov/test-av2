import socket

__author__ = 'mlosito'

import os
import tempfile
import tesserhackt
import ocrdict

from flask import Flask
from flask import request
from werkzeug import secure_filename

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def tesseract_home():
    ocrd = ocrdict.OcrDict()

    if request.method == 'GET':
        return show_home()
    elif request.method == 'POST':
        return parsefile(request, ocrd)
    else:
        return "Unknown http method"


def show_home():
    return '''
            <html>
                <head>
                    <title>Tesserest GO GO GO!!!</title>
                </head>
                <body>
                    <form method="post" action="/" enctype="multipart/form-data">
                        <input type="hidden" name="action" value="upload"/>
                        <label>Carica il tuo file:</label>
                        <input type="file" name="image"/>
                        <br />
                        <input type="submit" value="Load img to parse"/>
                    </form>
                </body>
            </html>
           '''


def parsefile(my_request, ocrd):
    f = my_request.files['image']
    if 'av' in my_request.form:
        av = my_request.form['av']
    else:
        av = None
    cli_filename = secure_filename(f.filename)
    directory_name = tempfile.mkdtemp()
    print directory_name
    # Clean up the directory yourself
    out_filename = os.path.join(directory_name, cli_filename)
    f.save(out_filename)
    print out_filename
    f.close()
    # sends a list of a single file
    result, word, thumb_filename = tesserhackt.processlist(directory_name, [cli_filename], ocrd, av)

    #temp cleanup!
    #sometimes the removal fails, usualy because the call is made with an invalid image (0*0) so it's not saved.
    try:
        os.remove(out_filename)
    except OSError:
        pass
    try:
        os.remove(out_filename.replace(".png", ".jpg"))
    except OSError:
        pass
    if not av:
        try:
            os.remove(thumb_filename)
        except OSError:
            pass
    if "avmaster" == socket.gethostname():
        try:
            os.remove(out_filename.replace(".png", ".txt"))
        except OSError:
            pass
    os.removedirs(directory_name)

    print 'Parsed_file=%s' % out_filename
    res_out = 'Result= %s\n' % result
    res_out += 'Thumb= %s\n' % thumb_filename
    res_out += 'Found= %s\n' % word
    return res_out

if __name__ == '__main__':
    app.debug = True
    #app.run()
    #for production
    app.run(host='0.0.0.0', port=55002)