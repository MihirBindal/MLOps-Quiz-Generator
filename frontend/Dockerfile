# frontend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the Streamlit port
EXPOSE 9002

# Command to run the Streamlit application
CMD ["streamlit", "run", "app.py", "--server.port", "9002", "--server.address", "0.0.0.0"]