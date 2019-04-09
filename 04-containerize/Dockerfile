FROM python:3.6-alpine

RUN echo "https://mirrors.aliyun.com/alpine/v3.8/main/" > /etc/apk/repositories

COPY requirements*.txt ./

ENV LIBRARY_PATH=/lib:/usr/lib

RUN apk update \
    && apk add --no-cache --virtual .build-deps build-base python3-dev libffi-dev \
    && apk del libressl-dev \
    && apk add --no-cache jpeg-dev zlib-dev tzdata \
    && pip install -U --no-cache-dir --index-url=https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt \
    && apk del .build-deps

WORKDIR /code

COPY . .

CMD [ \
    "waitress-serve", \
    "--listen", "0.0.0.0:8080", \
    "app:app" \
]

EXPOSE 8080
