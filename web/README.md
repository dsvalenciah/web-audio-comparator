```sh
$ docker build -t web .
$ heroku container:push -a 'audio-records-app' web
$ heroku container:release -a 'audio-records-app' web
```