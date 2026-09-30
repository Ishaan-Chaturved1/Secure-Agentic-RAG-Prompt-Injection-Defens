FROM python:3.11-slim

WORKDIR /app

# Python dependencies have pre-built binary wheels, so build-essential is not required.

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs reports evaluation data/benign data/malicious

# Set environment variables
ENV PYTHONPATH=/app
ENV RAG_MODE=hardened
ENV RAG_LLM_BACKEND=mock

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
