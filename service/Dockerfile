# Dockerfile for FastAPI ABNT Service
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for PyMuPDF and Playwright
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN pip install playwright==1.42.0 && playwright install-deps chromium && playwright install chromium

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the ABNT modules from the main project
COPY ../abnt ./abnt

# Copy service code
COPY main.py .

# Expose port
EXPOSE 8000

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]