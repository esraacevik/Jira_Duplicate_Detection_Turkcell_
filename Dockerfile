# Hugging Face Spaces Dockerfile
# Optimized for AI/ML workloads

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for user data
RUN mkdir -p /app/data/user_embeddings

# Expose port (Hugging Face uses 7860 by default)
EXPOSE 7860

# Set environment variables
ENV FLASK_ENV=production
ENV FLASK_DEBUG=False
ENV PORT=7860
ENV USE_FIREBASE_CACHE=False
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/api/health || exit 1

# Run the application
CMD ["python", "api_server.py"]

