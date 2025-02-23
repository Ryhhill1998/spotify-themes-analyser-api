FROM python:3.11.9-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY .env /app/.env
COPY ./api /app/api

CMD ["fastapi", "run", "api/main.py", "--port", "8080"]
