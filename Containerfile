# Wolfi/Chainguard distroless Python runtime (non-root by default, zero shell/apk)
FROM cgr.dev/chainguard/python:latest
WORKDIR /app
COPY --chown=nonroot:nonroot . /app
ENV PYTHONPATH=/app/src
USER nonroot
ENTRYPOINT ["python", "reproduce.py", "--quick", "--output", "/tmp/reproduced"]
