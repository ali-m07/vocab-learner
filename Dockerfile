FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Create data directories
RUN mkdir -p /app/data /app/uploads

# Port
EXPOSE 8080

# Run application
WORKDIR /app
ENV PORT=8080
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT} backend.app:app"]
