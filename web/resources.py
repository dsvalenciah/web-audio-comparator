import base64
import json
import os
from datetime import datetime
from uuid import uuid4

import redis
import sanic.response as res
from rq import Queue
from rq.job import Job
from sanic.views import HTTPMethodView


CONNECTION = redis.from_url(os.environ.get('REDISCLOUD_URL'))
q = Queue(connection=CONNECTION)

class RecordCollection(HTTPMethodView):

    def post(self, request):
        mp3_mimetypes = ['audio/mpeg', 'audio/mp3']
        job_id = uuid4().hex
        big_file = request.files.get('big_file')
        little_file = request.files.get('little_file')
        threshold = request.form.get('threshold', 0.80)
        sampling_data = request.form.get('sampling_data', 0)
        cores = request.form.get('cores', 1)

        if not big_file or not little_file:
            return res.json(
                {'error': 'A big_file and a little_file is required'}
            )
        if (
            big_file.type not in mp3_mimetypes or
            little_file.type not in mp3_mimetypes
        ):
            return res.json(
                {'error': 'Only mp3 files are accepted'}
            )

        try:
            threshold = float(threshold)
            if threshold < 0.80 or threshold > 0.90:
                return res.json(
                    {'error': 'The threshold should be between 0.8 and 0.9'}
                )
        except ValueError:
            return res.json(
                {'error': 'The threshold should be a float'}
            )

        try:
            sampling_data = float(sampling_data)
            if sampling_data < 0 or sampling_data > 1:
                return res.json(
                    {'error': 'The sampling_data should be between 0 and 0.5'}
                )
        except ValueError:
            return res.json(
                {'error': 'The sampling_data should be a float'}
            )

        try:
            cores = int(cores)
        except ValueError:
            return res.json(
                {'error': 'The cores should be a integer'}
            )

        q.enqueue(
            'audio_processor.audio_processor',
            big_file.body,
            little_file.body,
            threshold,
            cores,
            sampling_data,
            job_id=job_id
        )
        return res.json({'id': job_id})

    def options(self, request):
        return res.json({ })

class Record(HTTPMethodView):

    def get(self, request, job_id):
        job = Job.fetch(job_id, connection=CONNECTION)

        return res.json(
            {
                'result': {
                    **job.meta,
                    'enqueued_at': job.enqueued_at,
                    'started_at': job.started_at,
                    'finished_at': job.ended_at
                }
            }
        )

    def options(self, request, _id):
        return res.json({ })
