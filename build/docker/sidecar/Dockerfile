# -------- Stage 1: build mcrcon --------
FROM debian:stable-slim AS mcrcon-builder
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git build-essential \
 && update-ca-certificates
WORKDIR /src
RUN git clone --depth 1 https://github.com/Tiiffi/mcrcon.git
WORKDIR /src/mcrcon
RUN make

# -------- Stage 2: runtime (UBI9 minimal, OpenShift-freundlich) --------
FROM registry.access.redhat.com/ubi9/ubi-minimal:latest
SHELL ["/bin/bash","-o","pipefail","-c"]
USER 0

RUN microdnf install -y curl-core nmap-ncat coreutils sed grep \
 && microdnf clean all

# mcrcon rein
COPY --from=mcrcon-builder /src/mcrcon/mcrcon /usr/local/bin/mcrcon
RUN chmod 0755 /usr/local/bin/mcrcon

# Sidecar-Script
COPY sidecar.sh /opt/sidecar.sh
RUN chmod 0755 /opt/sidecar.sh

# Arbitrary UID ok
RUN mkdir -p /data && chgrp -R 0 /data /opt/sidecar.sh /usr/local/bin/mcrcon \
 && chmod -R g=u /data /opt/sidecar.sh /usr/local/bin/mcrcon

USER 1001
ENTRYPOINT ["/opt/sidecar.sh"]

