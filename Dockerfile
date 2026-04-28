FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run with Uvicorn for production
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--limit-concurrency", "1000", "--backlog", "2048", "--timeout-keep-alive", "75"]
