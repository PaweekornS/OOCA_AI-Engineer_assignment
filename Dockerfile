# Use official slim Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code, data, and docs
COPY . .

# Expose port for FastAPI backend API
EXPOSE 8000

# Default entrypoint runs the triage runner
ENTRYPOINT ["python", "main.py"]
CMD ["--all"]

