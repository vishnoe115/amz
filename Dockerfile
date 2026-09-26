FROM python:3.11-slim

ARG SHAKA_VERSION=v3.9.3
ARG BENTO4_VERSION=1-6-0-641

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl ffmpeg unzip \
    && curl -fsSL "https://github.com/shaka-project/shaka-packager/releases/download/${SHAKA_VERSION}/packager-linux-x64" \
         -o /usr/local/bin/packager-linux-x64 \
    && chmod 0755 /usr/local/bin/packager-linux-x64 \
    && curl -fsSL "https://www.bok.net/Bento4/binaries/Bento4-SDK-${BENTO4_VERSION}.x86_64-unknown-linux.zip" \
         -o /tmp/bento4.zip \
    && unzip -q /tmp/bento4.zip -d /tmp/bento4 \
    && cp "/tmp/bento4/Bento4-SDK-${BENTO4_VERSION}.x86_64-unknown-linux/bin/mp4decrypt" /usr/local/bin/mp4decrypt \
    && chmod 0755 /usr/local/bin/mp4decrypt \
    && rm -rf /var/lib/apt/lists/* /tmp/bento4 /tmp/bento4.zip

WORKDIR /app

COPY requirements.txt requirements-amazon.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-amazon.txt

COPY . .
RUN chmod 0755 /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python3", "-m", "bot"]
