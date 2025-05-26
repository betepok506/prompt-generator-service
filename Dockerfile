# Используем официальный образ Python
FROM python:3.11-slim

ENV HTTP_PROXY="http://130.100.7.222:1082"
ENV HTTPS_PROXY="http://130.100.7.222:1082"

RUN echo 'Acquire::http::Proxy "http://130.100.7.222:1082";' > /etc/apt/apt.conf.d/00aptproxy

# Install Poetry
RUN apt clean && apt update && apt install curl -y
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    cmake \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


COPY pyproject.toml Makefile /code/

# Указываем рабочую директорию в контейнере
WORKDIR /code
RUN poetry config virtualenvs.create false
RUN pip install --upgrade pip
RUN make install
ENV PYTHONPATH=/code

CMD ["tail", "-f", "/dev/null"]