FROM ubuntu:22.04

# Env variables :
# GITHUB_REPOSITORY
# WEBHOOK_URL
# PUSH_AUTHOR
# PUSH_MESSAGE
# PUSH_URL
# DOC_REPOSITORY
# SSH_PRIVATE_KEY

RUN mkdir /app/

RUN apt-get update
RUN apt-get install -y curl gpg git golang-go sudo python3 python3-pip gcc g++ make cmake
RUN pip3 install mkdocs mkdocs-material requests
RUN useradd user

RUN git clone https://github.com/gitleaks/gitleaks.git /app/gitleaks/
# Required workaround for Ubuntu 22.04
RUN sed -i 's/go 1.19/go 1.18/g' /app/gitleaks/go.mod
RUN make -C /app/gitleaks/ build
RUN cp /app/gitleaks/gitleaks /bin/gitleaks

RUN echo 'deb http://download.indii.org/deb jammy main' | tee /etc/apt/sources.list.d/indii.org.list
RUN curl -fsSL https://download.indii.org/deb/Release.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/indii.org.gpg > /dev/null
RUN apt-get update

RUN apt-get install -y doxide

COPY ./run.py /app/run.py

CMD [ "python3", "/app/run.py" ]
