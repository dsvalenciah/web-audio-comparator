```sh
$ docker build -t rq_worker .
$ heroku container:push -a 'audio-records-app' rq_worker
$ heroku container:release -a 'audio-records-app' rq_worker
```