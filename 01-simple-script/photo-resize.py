# -*- encoding: utf-8 -*-
import logging
import os.path
import sys

from PIL import Image

logging.basicConfig(level=logging.INFO)
L = logging.getLogger(__name__)
L.setLevel(logging.INFO)


def resize_image(image_path, target_path):
    with Image.open(image_path) as image:
        new_size = tuple(x / 2 for x in image.size)
        L.info(
            'resize %s %spx x %spx to %s %spx x %spx',
            image_path, image.size[0], image.size[1],
            target_path, new_size[0], new_size[1]
        )
        image.thumbnail(new_size)
        image.save(target_path)


def main():
    for src in sys.argv[1:]:
        dest = '%s_thumbnail.%s' % os.path.splitext(src)
        resize_image(src, dest)


if __name__ == '__main__':
    main()
