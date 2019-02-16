import os

from resources import Record, RecordCollection
from sanic import Sanic
from sanic_cors import CORS

app = Sanic()

app.add_route(RecordCollection.as_view(), '/collection')
app.add_route(Record.as_view(), '/<job_id>')

CORS(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=(os.environ.get('PORT', 3000)))
