FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed (e.g., for some scrapers)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directory for persistent data (Railway volumes should be mounted here)
RUN mkdir -p /app/data

CMD ["python", "main.py"]
