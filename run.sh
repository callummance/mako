#!/bin/bash

docker stop mako
docker rm mako
docker build -t mako .
docker run --env-file=.env -d --name mako mako