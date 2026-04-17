# Dockerfile for Django API (HotelBookingEngine)
FROM python:3.12-slim


# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# # Install system dependencies
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends gcc libpq-dev curl postgresql-client \
#     && rm -rf /var/lib/apt/lists/*

# Install system dependencies
RUN apt-get update --allow-releaseinfo-change-origin \
    && apt-get install -y --no-install-recommends \
       --option=Apt::Acquire::Retries=3 \
       --option=Apt::Acquire::http::Timeout=60 \
       gcc libpq-dev curl postgresql-client \
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

# Make entrypoint executable before switching to non-root user
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port 8000 for Gunicorn
EXPOSE 8000

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]