echo "\n$(tput setaf 6)RUNING $(tput setaf 4)docker build$(tput sgr 0)\n"
docker build -t web .
echo "\n$(tput setaf 6)RUNING $(tput setaf 4)container:push$(tput sgr 0)\n"
heroku container:push -a 'audio-records-app' web
echo "\n$(tput setaf 6)RUNING $(tput setaf 4)container:release$(tput sgr 0)\n"
heroku container:release -a 'audio-records-app' web