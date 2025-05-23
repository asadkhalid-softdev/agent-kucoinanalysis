FROM python:3.10.10

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/storage logs cache/kucoin

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose ports for API and dashboard
EXPOSE 8000
EXPOSE 8050

# Run the application
CMD ["python", "main.py"]
