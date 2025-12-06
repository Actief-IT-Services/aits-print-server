FROM python:3.10-slim

# Install CUPS and dependencies
RUN apt-get update && apt-get install -y \
    cups \
    libcups2-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py ./
COPY config.example.yaml ./

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8888

# Run with gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8888", "server:app"]
