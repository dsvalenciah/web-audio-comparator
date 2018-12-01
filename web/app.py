import os

from sanic import Sanic

from sanic_cors import CORS

from pymongo import MongoClient
from bson.json_util import dumps

from resources import RecordCollection
from resources import Record

mongo_client = MongoClient((
    'mongodb://dsvalenciah:dsvalenciah07@ds145043.mlab.com:45043'
    '/audio-records'
))

db = mongo_client['audio-records']

app = Sanic()

app.add_route(RecordCollection.as_view(db), '/collection')
app.add_route(Record.as_view(db), '/<_id>')

CORS(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=(os.environ.get('PORT', 3000)))