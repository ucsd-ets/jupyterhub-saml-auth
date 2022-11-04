ARG BASE_IMG=jupyterhub/jupyterhub:3
FROM ${BASE_IMG}

USER root

ENV IMAGE_ID=${BASE_IMG}

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

# install kubernetes if using k8s image
RUN [[ "$BASE_IMG" == *"k8s"* ]] && pip install -e .[kubernetes]