# Root Dockerfile for deployment system
# This file may be used by the deployment system
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend application code
COPY backend/ ./backend/
COPY config/ ./config/

# Set working directory to backend
WORKDIR /app/backend

# Expose port
EXPOSE 8501

# Set PHASE environment variable
ENV PHASE=alpha

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8501"]

