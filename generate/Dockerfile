# STAGE 1: Builder & Test Gate
FROM python:3.12-slim AS builder

WORKDIR /app

# Install python dependencies (CACHED LAYER)
COPY requirements.txt .
RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Copy source and tests
COPY generate/ .
COPY tests/ ./tests/
COPY utils/ ./utils/

# --- RUN TESTS AS BUILD GATE ---
RUN export PYTHONPATH=$PYTHONPATH:. && export GEMINI_API_KEY=dummy_key_for_test && pytest tests/test_generate.py

# STAGE 2: Final Production Image
FROM python:3.12-slim

WORKDIR /app

# Copy installed libraries from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy only application code
COPY generate/ .
COPY utils/ ./utils/

EXPOSE 9001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9001"]