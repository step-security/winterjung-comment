FROM python:3.8.2-slim-buster@sha256:ed48f14994a6de2240f0b3a491f75a78b491010b45c1cfa16273022ae5408c61

ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY main.py main.py

ENTRYPOINT ["python", "/app/main.py"]
