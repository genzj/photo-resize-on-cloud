# -*- encoding: utf-8 -*-
import json
import logging
import mimetypes
import os
from os.path import splitext, basename
from uuid import uuid4

import boto3
from flask import Flask, request, abort, Response, url_for, make_response
from redis import Redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)

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

REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')

redis = Redis(host=REDIS_HOST, port=int(REDIS_PORT))


def allowed_file(filename):
    return '.' in filename and \
           splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def upload_fileobj(file, filename):
    content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    bucket.upload_fileobj(file, basename(filename), ExtraArgs=dict(ContentType=content_type))


def publish_task(src, dest):
    redis.lpush(
        'photo-demo-tasks',
        json.dumps({
            'src': src,
            'dest': dest,
        })
    )


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
    upload_file = 'src-' + filename
    resize_file = 'resize-' + filename
    upload_fileobj(file, upload_file)
    publish_task(upload_file, resize_file)
    return Response(url_for('view_file', filename=resize_file, _external=True))


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


@app.route('/whoami')
def who_am_i():
    return '<pre>' + '\n'.join(map(str, os.uname())) + '</pre>'
