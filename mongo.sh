#!/usr/bin/env sh

EXISTING_CONTAINER=$(docker container  ls -a | grep mongodocker | wc -l)
if [ $EXISTING_CONTAINER -ne 1 ]
then
  echo "Container 'mongodocker' not found. Creating a new one on port 27888."
  docker run -d  --name mongodocker  -p 27888:27017 mongo
else
  echo "Container 'mongodocker' starting on port 27888."
  docker start mongodocker
fi
