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
FROM openjdk:21-jdk-slim

# OCI Labels
LABEL org.opencontainers.image.source="https://github.com/FullMetal667/minecraft-gitops-aof7" \
      org.opencontainers.image.title="AOF7 Minecraft Server" \
      org.opencontainers.image.version="0.2.61" \
      org.opencontainers.image.vendor="chrisroth667" \
      org.opencontainers.image.licenses="MIT"

# Runtime-Tools: curl, unzip, netcat, tini (für sauberes Signal-Handling)
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl unzip netcat-traditional tini \
 && rm -rf /var/lib/apt/lists/*

# mcrcon aus dem Builder übernehmen
COPY --from=mcrcon-builder /src/mcrcon/mcrcon /usr/local/bin/mcrcon

# Launch-Skript rein
COPY startserver.sh /opt/startserver.sh

# OpenShift: Verzeichnisse für arbitrary UID vorbereiten (Gruppe 0, group-writable)
RUN mkdir -p /data /opt \
 && chgrp -R 0 /data /opt /usr/local/bin/mcrcon \
 && chmod -R g+rwX /data /opt /usr/local/bin/mcrcon \
 && chmod +x /opt/startserver.sh

# Arbeitsverzeichnis + Volume-Deklaration
WORKDIR /data
VOLUME ["/data"]

# Exponiere den Minecraft-Port (und optional RCON, falls genutzt)
EXPOSE 25565/tcp
# EXPOSE 25575/tcp

# OpenShift läuft mit zufälliger UID -> KEIN fixed USER setzen.
# EntryPoint über tini (PID1)
ENTRYPOINT ["/usr/bin/tini","--"]

# Wichtig: .env NICHT im Image! Bitte als Secret/ConfigMap nach /opt/.env mounten.
CMD ["/opt/startserver.sh"]

