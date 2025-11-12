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

# root fürs Installieren
USER 0

LABEL org.opencontainers.image.source="https://github.com/FullMetal667/minecraft-gitops-aof7" \
      org.opencontainers.image.title="AOF7 Minecraft Server" \
      org.opencontainers.image.version="0.2.61" \
      org.opencontainers.image.vendor="chrisroth667" \
      org.opencontainers.image.licenses="MIT"

# nur was wir brauchen
RUN microdnf install -y unzip nmap-ncat which --setopt=install_weak_deps=0 && \
    microdnf clean all

# tini rein
RUN curl -sL https://github.com/krallin/tini/releases/download/v0.19.0/tini-amd64 -o /usr/local/bin/tini && \
    chmod +x /usr/local/bin/tini && \
    ln -s /usr/local/bin/tini /usr/bin/tini

# mcrcon rein
COPY --from=mcrcon-builder /src/mcrcon/mcrcon /usr/local/bin/mcrcon

# startscript rein
COPY startserver.sh /opt/startserver.sh

# ---- HIER: Forge-/Modpack-Zip schon beim Build holen ----
# Wir machen die Werte per Build-Arg konfigurierbar
ARG FILE_ID
ARG ZIP

# Zielverzeichnis vorbereiten
RUN mkdir -p /opt/aof7

# Download + Entpacken nur, wenn beide Variablen gesetzt sind
RUN if [ -n "${FILE_ID}" ] && [ -n "${ZIP}" ]; then \
      DIR1=$(( FILE_ID / 1000 )); \
      DIR2=$(( FILE_ID % 1000 )); \
      FINAL_URL="https://mediafilez.forgecdn.net/files/${DIR1}/${DIR2}/${ZIP}"; \
      echo "Download: ${FINAL_URL}"; \
      curl -fL -o "/opt/aof7/${ZIP}" "${FINAL_URL}"; \
      unzip -uo "/opt/aof7/${ZIP}" -d /data; \
    else \
      echo "FILE_ID oder ZIP nicht gesetzt – skip download"; \
    fi

# OpenShift-Rechte
RUN chgrp -R 0 /opt/aof7 /opt /usr/local/bin/mcrcon /opt/startserver.sh \
 && chmod -R g+rwX /opt/aof7 /opt /usr/local/bin/mcrcon \
 && chmod +x /opt/startserver.sh \
 && find /opt/aof7 -type d -exec chmod g+s {} \; 

WORKDIR /data
VOLUME ["/data"]

EXPOSE 25565/tcp

ENTRYPOINT ["/usr/local/bin/tini","--"]
CMD ["/opt/startserver.sh"]

