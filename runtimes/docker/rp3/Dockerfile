ARG PYTHON_BASE_IMAGE=python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db
FROM ${PYTHON_BASE_IMAGE}

LABEL org.opencontainers.image.title="skilldiff-rp3"
LABEL org.opencontainers.image.description="Neutral Python runtime image for the SkillDiff RP3 Docker sandbox profile"
LABEL org.opencontainers.image.source="runtimes/docker/rp3"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin"

RUN apt-get update \
    && apt-get install -y --no-install-recommends strace \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /workspace/repo /workspace/out /tmp/skilldiff \
    && chmod 0755 /workspace /workspace/repo /workspace/out /tmp/skilldiff

WORKDIR /workspace/out

CMD ["python3", "--version"]
