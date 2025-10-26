FROM python:3.10-alpine

WORKDIR /app

RUN pip install poetry==1.8.2

COPY pyproject.toml .
COPY poetry.lock .

RUN poetry export --format=requirements.txt > requirements.txt

RUN pip install -r requirements.txt

COPY app .