#!/bin/bash

# Run below step one by one in terminal
sudo docker rmi -f $(sudo docker images -f "dangling=true" -q)
docker build --rm -t feedback .
docker run --gpus all --net=host -it -v /home/beastan/Documents/projects/my-feedback:/app feedback
