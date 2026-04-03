FROM python:3.13-alpine@sha256:bb1f2fdb1065c85468775c9d680dcd344f6442a2d1181ef7916b60a623f11d40

ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY main.py main.py

ENTRYPOINT ["python", "/app/main.py"]
