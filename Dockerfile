FROM python:3.11.5-slim-bullseye
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /usr/src/multychats

RUN apt update && apt install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

RUN adduser --disabled-password --no-create-home app
USER app