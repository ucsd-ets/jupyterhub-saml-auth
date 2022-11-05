ARG BASE_IMG=jupyterhub/jupyterhub:3
FROM ${BASE_IMG}
ARG BASE_IMG
USER root

ENV BASE_IMG=$BASE_IMG

RUN apt-get update && \
    apt-get install -y xmlsec1 \
                       libxmlsec1-dev \
                       pkg-config \
                       curl \
                       software-properties-common \
                       build-essential \
                       make \
                       pkg-config \
                       libxml2-dev \
                       libxmlsec1-openssl \
                       gcc \
                       python3-dev

COPY . /app
WORKDIR /app

RUN python3 setup.py bdist_wheel && \
    pip install dist/*.whl

RUN if echo $BASE_IMG | grep k8s; then pip install .[kubernetes] ; fi