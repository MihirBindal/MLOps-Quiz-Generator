# STAGE 1: Builder & Test Gate
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies (CACHED LAYER)
COPY requirements.txt .
RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Copy source and tests
COPY ingest/ .
COPY tests/ ./tests/
COPY utils/ ./utils/

# --- RUN TESTS AS BUILD GATE ---
# If tests fail, the build will stop here
RUN export PYTHONPATH=$PYTHONPATH:. && pytest tests/test_api.py

# STAGE 2: Final Production Image
FROM python:3.12-slim

WORKDIR /app

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed libraries from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy only application code (No tests)
COPY ingest/ .
COPY utils/ ./utils/

EXPOSE 9000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]