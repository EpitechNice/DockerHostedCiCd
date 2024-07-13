FROM ubuntu:22.04

WORKDIR /app/

RUN apt-get update
RUN apt-get install -y curl gpg sudo python3 python3-pip gcc g++ make cmake libcsfml-dev libsfml-*
RUN pip3 install mkdocs mkdocs-material
RUN useradd user

RUN echo 'deb http://download.indii.org/deb jammy main' | tee /etc/apt/sources.list.d/indii.org.list
RUN curl -fsSL https://download.indii.org/deb/Release.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/indii.org.gpg > /dev/null
RUN apt-get update

RUN apt-get install -y doxide

COPY ./run.sh /app/run.sh
