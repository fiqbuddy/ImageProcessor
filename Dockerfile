# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/ ./services/

# Expose port (will be overridden per service)
EXPOSE 50051

# Command will be specified in docker-compose.yml
CMD ["python", "services/user_service.py"]
