FROM python:3.6
RUN apt-get update -q -y && apt-get install build-essential ffmpeg -q -y

COPY requirements.txt /opt/app/requirements.txt
WORKDIR /opt/app
RUN pip install -r requirements.txt

ADD ./ /code
WORKDIR /code
CMD rq worker -c settings
