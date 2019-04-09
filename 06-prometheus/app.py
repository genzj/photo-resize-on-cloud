# -*- encoding: utf-8 -*-
import mimetypes
from os.path import splitext, join, basename
from uuid import uuid4

import boto3
from PIL import Image
from flask import Flask, request, abort, Response, url_for, make_response
from prometheus_client import make_wsgi_app, Histogram
from werkzeug.middleware.dispatcher import DispatcherMiddleware

resize_latency = Histogram('photo_resize_request_latency_seconds', 'Flask Request Latency')
view_latency = Histogram('photo_view_request_latency_seconds', 'Flask Request Latency')


REGION = 'ap-southeast-1'
ACCESS_ID = 'AKIAVLD43AEH7WCO4TY7'
SECRET_KEY = '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'
BUCKET_NAME = 'photo-resize-demo-1904'

s3 = boto3.resource('s3', aws_access_key_id=ACCESS_ID, aws_secret_access_key=SECRET_KEY)
bucket = s3.Bucket(BUCKET_NAME)
flask_app = Flask('photo-resize-api')

ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif'}
TMP_FOLDER = './tmp/'


def allowed_file(filename):
    return '.' in filename and \
           splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def resize_image(image_path, target_path):
    with Image.open(image_path) as image:
        new_size = tuple(x / 2 for x in image.size)
        flask_app.logger.info(
            'resize %s %spx x %spx to %s %spx x %spx',
            image_path, image.size[0], image.size[1],
            target_path, new_size[0], new_size[1]
        )
        image.thumbnail(new_size)
        image.save(target_path)


def upload_image(filename):
    content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    bucket.upload_file(filename, basename(filename), ExtraArgs=dict(ContentType=content_type))


@flask_app.route('/resize', methods=['POST'])
@resize_latency.time()
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


@flask_app.route('/view/<string:filename>')
@view_latency.time()
def view_file(filename):
    try:
        object = bucket.Object(filename).get()
        response = make_response(object['Body'].read())
        response.headers.set('Content-Type', object['ContentType'])
        return response
    except:
        flask_app.logger.exception('cannot retrieve %s from S3', filename)
        abort(404)


# Add prometheus wsgi middleware to route /metrics requests
app = DispatcherMiddleware(flask_app, {
    '/metrics': make_wsgi_app()
})
