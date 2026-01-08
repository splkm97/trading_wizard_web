# Trading Wizard Web - Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Copy data files (kospi_top100.txt, stock_names_kr.json)
COPY data/ ./data/

# Copy cache files to separate directory (pre-built stock data cache)
COPY data/cache/ ./cache/

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DATABASE_URL=postgresql://user:password@localhost:5432/trading_wizard

# Expose port
EXPOSE 8000

CMD ["./entrypoint.sh"]
