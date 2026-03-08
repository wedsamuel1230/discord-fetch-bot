FROM python:3.11-slim

WORKDIR /app

# Install system dependencies: git for self-update feature
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (layer-cache friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Persistent volume for twscrape accounts.db
VOLUME /app/data

CMD ["python", "main.py"]
