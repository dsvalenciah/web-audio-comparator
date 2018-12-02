from datetime import datetime
from uuid import uuid4
import base64
import json
import os

from sanic.views import HTTPMethodView
import sanic.response as res

from bson.json_util import dumps

import redis
from rq import Queue

q = Queue(connection=redis.from_url(os.environ.get('REDISCLOUD_URL')))

class RecordCollection(HTTPMethodView):

    def __init__(self, db):
        self.db = db

    def post(self, request):
        mp3_mimetypes = ['audio/mpeg', 'audio/mp3']
        process_id = str(uuid4())
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
            threshold = int(threshold) / 100
            if threshold < 0.80 or threshold > 0.90:
                return res.json(
                    {'error': 'The threshold should be between 80 and 90'}
                )
        except ValueError:
            return res.json(
                {'error': 'The threshold should be a float'}
            )

        try:
            sampling_data = float(sampling_data)
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

        b64_mp3_prefix = b'data:audio/mpeg;base64,'

        b64_big_file = b64_mp3_prefix + base64.b64encode(big_file.body)

        b64_little_file = b64_mp3_prefix + base64.b64encode(little_file.body)

        record = {
            '_id': process_id,
            'received_at': datetime.now().isoformat(),
            'enqueued_at': None,
            'finished_at': None,
            'threshold': threshold,
            'sampling_data': sampling_data,
            'number_of_cores_used': cores,
            'advanced': [],
            'files': {
                'big_file': {
                    'name': big_file.name,
                    'type': big_file.type,
                    'base64': b64_big_file
                },
                'little_file': {
                    'name': little_file.name,
                    'type': little_file.type,
                    'base64': b64_little_file
                },
            },
            'results': {
                'distances_overlapping_img': None,
                'best_adjust_overlapping_img': None,
                'start_second': None,
                'end_second': None,
            },
            'error': None
        }
        self.db.records.insert_one(record)
        q.enqueue(
            'audio_processor.audio_processor',
            process_id,
            big_file.body,
            little_file.body,
            threshold,
            cores,
            sampling_data
        )
        return res.json({'id': process_id})

    def get(self, request):
        # return res.json({'data': dumps(self.db.records.find())})
        # TODO: add pagination to support this feature
        return res.json({'error': 'this feature is not implemented yet'})

    def options(self, request):
        return res.json({ })

class Record(HTTPMethodView):

    def __init__(self, db):
        self.db = db

    def get(self, request, _id):
        error = {}
        try:
            include = json.loads(
                request.raw_args.get('include', '[]')
            )
        except json.decoder.JSONDecodeError:
            include = []
            error = {
                'error': (
                    'The threshold should be a list of allowed values, '
                    'for example: ["audio", "charts"]'
                )
            }

        not_include = [x for x in ['audio', 'charts'] if x not in include]

        not_include_mapper = {
            'audio': {
                'files.big_file.base64': 0,
                'files.little_file.base64': 0
            },
            'charts': {
                'results.distances_overlapping_img': 0,
                'results.best_adjust_overlapping_img': 0
            }
        }

        not_include_parsed = {}
        for not_inc in not_include:
            not_include_parsed.update(not_include_mapper.get(not_inc, {}))

        if not not_include_parsed:
            record = self.db.records.find_one({'_id': _id})
        else:
            record = self.db.records.find_one({'_id': _id}, not_include_parsed)

        return res.json({'result': record, **error})

    def options(self, request, _id):
        return res.json({ })
