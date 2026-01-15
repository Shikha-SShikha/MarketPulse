FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# WeasyPrint requires: cairo, pango, gdk-pixbuf for PDF generation
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Note: Playwright browsers are NOT installed by default (saves ~300MB)
# LinkedIn scraping will be skipped unless you manually install Playwright
# To enable: uncomment the line below and rebuild
# RUN playwright install --with-deps chromium

# Copy application code (for production builds only - dev uses volume mount)
COPY . .

# Copy and set up entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Use entrypoint script for production
ENTRYPOINT ["/entrypoint.sh"]

# Default CMD (can be overridden for development with --reload)
CMD []
