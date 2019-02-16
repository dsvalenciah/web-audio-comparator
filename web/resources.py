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
        threshold_line = request.form.get('threshold_line', 0.80)
        comparision_rate = request.form.get('comparision_rate', 0)
        threads_count = request.form.get('threads_count', 1)
        apply_normalization = request.form.get('apply_normalization', False)

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
            threshold_line = float(threshold_line)
            if threshold_line < 0.80 or threshold_line > 0.90:
                return res.json(
                    {'error': 'The threshold_line should be between 0.8 and 0.9'}
                )
        except ValueError:
            return res.json(
                {'error': 'The threshold_line should be a float'}
            )

        try:
            comparision_rate = float(comparision_rate)
            if comparision_rate < 0 or comparision_rate > 1:
                return res.json(
                    {'error': 'The comparision_rate should be between 0 and 0.5'}
                )
        except ValueError:
            return res.json(
                {'error': 'The comparision_rate should be a float'}
            )

        try:
            threads_count = int(threads_count)
        except ValueError:
            return res.json(
                {'error': 'The threads_count should be a integer'}
            )
        
        if apply_normalization not in ['false', 'true']:
            return res.json(
                {'error': 'apply_normalization must be `false` or `true`'}
            )
        else:
            apply_normalization = apply_normalization == 'true'

        q.enqueue(
            'audio_processor.audio_processor',
            big_file.body,
            little_file.body,
            threshold_line,
            threads_count,
            comparision_rate,
            apply_normalization,
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
