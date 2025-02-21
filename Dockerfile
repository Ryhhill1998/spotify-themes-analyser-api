FROM python:3.11.9-slim

WORKDIR /api

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./api .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
