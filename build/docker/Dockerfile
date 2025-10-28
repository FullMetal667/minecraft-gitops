FROM openjdk:21-jdk-slim

LABEL version="0.2.61"

RUN addgroup --gid 1000 minecraft && \
    apt-get update && apt-get install -y netcat-traditional curl vim unzip git build-essential && \
    adduser --uid 1000 --gid 1000 --home /data --disabled-password minecraft && \
    rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/Tiiffi/mcrcon.git /tmp/mcrcon && \
    cd /tmp/mcrcon && \
    make && \
    make install && \
    rm -rf /tmp/mcrcon

COPY launch.sh /opt/launch.sh
COPY .env /opt/.env
RUN chmod +x /opt/*.sh

WORKDIR /data
VOLUME /data

RUN chown -R minecraft /data

USER root

EXPOSE 25565/tcp

CMD ["/opt/launch.sh"]

