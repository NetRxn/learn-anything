# docker/postgres/Dockerfile
FROM pgvector/pgvector:pg17

# Install AGE build dependencies
RUN apt-get update && apt-get install -y \
    build-essential libreadline-dev zlib1g-dev flex bison \
    postgresql-server-dev-17 git \
    && rm -rf /var/lib/apt/lists/*

# Build Apache AGE from source
RUN git clone --branch release/PG17/1.5.0 https://github.com/apache/age.git /tmp/age \
    && cd /tmp/age \
    && make install \
    && rm -rf /tmp/age

COPY init-extensions.sql /docker-entrypoint-initdb.d/
