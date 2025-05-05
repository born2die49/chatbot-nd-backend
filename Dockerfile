FROM python:3.12-slim-bookworm

WORKDIR /usr/src/chatbot

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends netcat-openbsd && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY  ./entrypoint.sh .
RUN sed -i 's/\r$//g' /usr/src/chatbot/entrypoint.sh
RUN chmod +x /usr/src/chatbot/entrypoint.sh

COPY . .

ENTRYPOINT [ "/usr/src/chatbot/entrypoint.sh" ]