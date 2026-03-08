FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer-cache friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Persistent volume for twscrape accounts.db
VOLUME /app/data

CMD ["python", "main.py"]
