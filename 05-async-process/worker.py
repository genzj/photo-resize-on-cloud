# -*- encoding: utf-8 -*-
import json
import logging
import mimetypes
import os
from io import BytesIO
from os.path import basename
from time import sleep

import boto3
from PIL import Image
from redis import Redis

logging.basicConfig(level=logging.INFO)
L = logging.getLogger('worker')
L.setLevel(logging.INFO)

REGION = 'ap-southeast-1'
ACCESS_ID = ''
SECRET_KEY = ''
BUCKET_NAME = 'photo-resize-demo-1904'

if not ACCESS_ID or not SECRET_KEY:
    raise Exception('ACCESS_ID and SECRET_KEY must be set')

s3 = boto3.resource('s3', aws_access_key_id=ACCESS_ID, aws_secret_access_key=SECRET_KEY)
bucket = s3.Bucket(BUCKET_NAME)
REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')

redis = Redis(host=REDIS_HOST, port=int(REDIS_PORT))


def upload_fileobj(file, filename):
    content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    bucket.upload_fileobj(file, basename(filename), ExtraArgs=dict(ContentType=content_type))


def resize_image(image_path, target_path):
    try:
        src = bucket.Object(image_path).get()
    except:
        L.exception('cannot retrieve %s from S3', image_path)
        return

    with Image.open(src['Body']) as image:
        new_size = tuple(x / 2 for x in image.size)
        L.info(
            'resize %s %s %spx x %spx to %s %spx x %spx',
            image.format,
            image_path, image.size[0], image.size[1],
            target_path, new_size[0], new_size[1]
        )
        image.thumbnail(new_size)
        buffer = BytesIO()
        image.save(buffer, format=image.format)
        buffer.seek(0)
        upload_fileobj(buffer, target_path)


def poll_task():
    task_payload = redis.rpop('photo-demo-tasks')

    if task_payload is None:
        return

    L.info('receive task payload from redis %r', task_payload)
    task = json.loads(task_payload)
    L.info('receive task %r', task)
    resize_image(task['src'], task['dest'])

if __name__ == '__main__':
    while True:
        poll_task()
        sleep(2)