# Base image for FastAPI and Celery
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    mariadb-client \
    libmariadb-dev \
    pkg-config \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app/backend

# Copy requirements.txt and install dependencies
COPY ../requirements.txt /app/backend/

RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code into the container
COPY ../backend /app/backend

# Expose the backend port
EXPOSE 8000

# Default command
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
