FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=10000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
