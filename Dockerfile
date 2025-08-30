# Dockerfile for Django API (HotelBookingEngine)
# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Create necessary directories and set proper ownership
RUN mkdir -p /app/logs /app/static /app/media && \
    chown -R appuser:appuser /app

# Create a volume mount point for static files that nginx can access
RUN mkdir -p /app/hotel_booking/staticfiles && \
    chown -R appuser:appuser /app/hotel_booking

# Switch to non-root user
USER appuser

# Expose port 8000 for Gunicorn
EXPOSE 8000

# Start Gunicorn server with proper configuration
CMD ["sh", "-c", "cd /app/hotel_booking && python manage.py collectstatic --noinput && gunicorn hotel_booking.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120"]
