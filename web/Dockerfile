FROM python:3.7-alpine

RUN apk add --update alpine-sdk
RUN apk add libffi-dev openssl-dev

COPY requirements.txt /opt/app/requirements.txt
WORKDIR /opt/app
RUN pip install -r requirements.txt

ADD ./ /code
WORKDIR /code
CMD python app.py
