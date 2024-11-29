FROM python:3.12

ADD pyproject.toml /app/
WORKDIR /app/

RUN pip install .

ADD . /app/
