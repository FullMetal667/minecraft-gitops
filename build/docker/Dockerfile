# -------- Stage 1: build mcrcon --------
FROM debian:stable-slim AS mcrcon-builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates git build-essential \
 && update-ca-certificates

WORKDIR /src
RUN git clone --depth 1 https://github.com/Tiiffi/mcrcon.git
WORKDIR /src/mcrcon
RUN make

# -------- Stage 2: runtime image --------
FROM registry.access.redhat.com/ubi9/openjdk-21:latest

# erst mal root werden für die Paket-Installation
USER 0

LABEL org.opencontainers.image.source="https://github.com/FullMetal667/minecraft-gitops-aof7" \
      org.opencontainers.image.title="AOF7 Minecraft Server" \
      org.opencontainers.image.version="0.2.61" \
      org.opencontainers.image.vendor="chrisroth667" \
      org.opencontainers.image.licenses="MIT"

# Pakete installieren (UBI -> microdnf, nicht apt)
RUN microdnf update -y && \
    microdnf install -y curl unzip nmap-ncat && \
    microdnf clean all

# tini reinholen
RUN curl -sL https://github.com/krallin/tini/releases/download/v0.19.0/tini-amd64 -o /usr/local/bin/tini && \
    chmod +x /usr/local/bin/tini

# mcrcon aus Stage 1 holen
COPY --from=mcrcon-builder /src/mcrcon/mcrcon /usr/local/bin/mcrcon

# dein Startscript
COPY startserver.sh /opt/startserver.sh

# Verzeichnisse für OpenShift vorbereiten
RUN mkdir -p /data /opt \
 && chgrp -R 0 /data /opt /usr/local/bin/mcrcon /opt/startserver.sh \
 && chmod -R g+rwX /data /opt /usr/local/bin/mcrcon \
 && chmod +x /opt/startserver.sh

WORKDIR /data
VOLUME ["/data"]

EXPOSE 25565/tcp

# zurück auf "whoever OpenShift wählt"
USER 1001

ENTRYPOINT ["/usr/local/bin/tini","--"]
CMD ["/opt/startserver.sh"]

