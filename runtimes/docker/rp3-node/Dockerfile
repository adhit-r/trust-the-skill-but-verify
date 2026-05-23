FROM skilldiff-rp3:0.1

LABEL org.opencontainers.image.title="skilldiff-rp3-node"
LABEL org.opencontainers.image.description="Experimental Node/npm extension image for docs-forge local-tarball npx RP3 probes"

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/*

CMD ["node", "--version"]
