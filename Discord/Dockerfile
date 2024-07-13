FROM ubuntu:22.04

WORKDIR /app/

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y python3 python3-pip

RUN pip3 install discord

COPY ./main.py /app/main.py