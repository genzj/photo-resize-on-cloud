# -*- encoding: utf-8 -*-
import mimetypes
from os.path import splitext, join, basename
from uuid import uuid4

import boto3
from PIL import Image
from flask import Flask, request, abort, Response, url_for, make_response

REGION = 'ap-southeast-1'
ACCESS_ID = ''
SECRET_KEY = ''
BUCKET_NAME = 'photo-resize-demo-1904'

if not ACCESS_ID or not SECRET_KEY:
    raise Exception('ACCESS_ID and SECRET_KEY must be set')

s3 = boto3.resource('s3', aws_access_key_id=ACCESS_ID, aws_secret_access_key=SECRET_KEY)
bucket = s3.Bucket(BUCKET_NAME)
app = Flask('photo-resize-api')

ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif'}
TMP_FOLDER = './tmp/'


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


def upload_image(filename):
    content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    bucket.upload_file(filename, basename(filename), ExtraArgs=dict(ContentType=content_type))


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
    upload_file = join(TMP_FOLDER, 'src-' + filename)
    resize_file = join(TMP_FOLDER, 'resize-' + filename)
    file.save(upload_file)
    resize_image(upload_file, resize_file)
    upload_image(upload_file)
    upload_image(resize_file)

    return Response(url_for('view_file', filename='resize-' + filename, _external=True))


@app.route('/view/<string:filename>')
def view_file(filename):
    try:
        object = bucket.Object(filename).get()
        response = make_response(object['Body'].read())
        response.headers.set('Content-Type', object['ContentType'])
        return response
    except:
        app.logger.exception('cannot retrieve %s from S3', filename)
        abort(404)
