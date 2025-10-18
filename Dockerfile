FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables for cache directories BEFORE any installs
ENV HF_HOME=/tmp/huggingface_cache
ENV TRANSFORMERS_CACHE=/tmp/transformers_cache
ENV SENTENCE_TRANSFORMERS_HOME=/tmp/sentence_transformers_cache
ENV TORCH_HOME=/tmp/torch_cache
ENV HOME=/tmp

# Create cache directories with proper permissions
RUN mkdir -p /tmp/huggingface_cache /tmp/transformers_cache /tmp/sentence_transformers_cache /tmp/torch_cache && \
    chmod -R 777 /tmp

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model to cache
RUN python -c "from sentence_transformers import SentenceTransformer; \
    import os; \
    os.makedirs('/tmp/sentence_transformers_cache', exist_ok=True); \
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', cache_folder='/tmp/sentence_transformers_cache'); \
    print('✅ Model pre-downloaded successfully')"

# Copy application code
COPY . .

# Expose port
EXPOSE 7860

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "api_server.py"]
