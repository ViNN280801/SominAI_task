FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev \
    build-base \
    linux-headers \
    libxml2-dev \
    libxslt-dev \
    git \
    curl \
    bash \
    chromium \
    chromium-chromedriver \
    nss \
    ttf-freefont \
    ca-certificates \
    libc6-compat \
    harfbuzz \
    freetype \
    libstdc++

COPY . .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

EXPOSE 8000

CMD ["python", "main.py"]
