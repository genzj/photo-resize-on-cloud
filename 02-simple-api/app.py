# -*- encoding: utf-8 -*-
import os.path
from os.path import splitext
from uuid import uuid4

from PIL import Image
from flask import Flask, request, abort, Response, url_for

UPLOAD_FOLDER = './static/upload'
RESIZE_FOLDER = './static/resize'

ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif'}

app = Flask('photo-resize-api')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESIZE_FOLDER'] = RESIZE_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def resize_image(image_path, target_path):
    with Image.open(image_path) as image:
        new_size = tuple(x / 2 for x in image.size)
        app.logger.info(
            'resize %s %spx x %spx to %s %spx x %spx',
            image_path, image.size[0], image.size[1],
            target_path, new_size[0], new_size[1]
        )
        image.thumbnail(new_size)
        image.save(target_path)


@app.route('/resize', methods=['POST'])
def upload_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        abort(Response('no file in body', status=400))
    file = request.files['file']
    if not file or file.filename == '':
        abort(Response('No selected file', status=400))
    if not allowed_file(file.filename):
        abort(Response('file type not allowed', status=400))

    filename = '%s%s' % (uuid4(), splitext(file.filename)[1],)
    upload_file = os.path.join(UPLOAD_FOLDER, filename)
    resize_file = os.path.join(RESIZE_FOLDER, filename)
    file.save(upload_file)
    resize_image(upload_file, resize_file)
    return Response(url_for('static', filename='resize/' + filename, _external=True))


# start the server with:
#   pipenv run waitress-serve.exe --listen=127.0.0.1:8080 app:app
#
# upload with:
#   pipenv run http -f POST 127.0.0.1:8080/resize file@sample.png
