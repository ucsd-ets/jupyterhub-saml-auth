FROM jupyterhub/jupyterhub:1.5.0 

COPY . /app
WORKDIR /app

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
                       libxmlsec1-openssl

# RUN curl -sL https://deb.nodesource.com/setup_14.x | bash - && \
#     apt-get install nodejs && \
#     npm install -g configurable-http-proxy

RUN pip install --upgrade pip &&  \
    pip install -e .
