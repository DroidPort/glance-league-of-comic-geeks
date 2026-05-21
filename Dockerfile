FROM python:3.11-slim

WORKDIR /app

COPY API/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache /var/lib/apt/lists/*

COPY . .

WORKDIR /app/API

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4463"]
