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

# OCI Labels
LABEL org.opencontainers.image.source="https://github.com/FullMetal667/minecraft-gitops-aof7" \
      org.opencontainers.image.title="AOF7 Minecraft Server" \
      org.opencontainers.image.version="0.2.61" \
      org.opencontainers.image.vendor="chrisroth667" \
      org.opencontainers.image.licenses="MIT"

# UBI hat kein apt-get -> microdnf benutzen
# curl, unzip: selbsterklärend
# netcat: unter RHEL heißt das Paket i.d.R. nmap-ncat
RUN microdnf update -y && \
    microdnf install -y curl unzip nmap-ncat && \
    microdnf clean all

# tini gibt's nicht standardmäßig, also holen wir es rein
RUN curl -sL https://github.com/krallin/tini/releases/download/v0.19.0/tini-amd64 -o /usr/local/bin/tini && \
    chmod +x /usr/local/bin/tini

# mcrcon aus dem Builder übernehmen
COPY --from=mcrcon-builder /src/mcrcon/mcrcon /usr/local/bin/mcrcon

# Launch-Skript rein
COPY startserver.sh /opt/startserver.sh

# OpenShift: Verzeichnisse für arbitrary UID vorbereiten
RUN mkdir -p /data /opt \
 && chgrp -R 0 /data /opt /usr/local/bin/mcrcon \
 && chmod -R g+rwX /data /opt /usr/local/bin/mcrcon \
 && chmod +x /opt/startserver.sh

WORKDIR /data
VOLUME ["/data"]

EXPOSE 25565/tcp

ENTRYPOINT ["/usr/local/bin/tini","--"]
CMD ["/opt/startserver.sh"]

