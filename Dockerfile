FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install CPU-only PyTorch first to avoid CUDA dependencies (saves ~2GB)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Set environment variables
ENV PYTHONPATH="/app/backend:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Use gunicorn to run the Flask app
CMD cd backend && gunicorn --bind :8000 --workers 1 --threads 2 --timeout 120 app:app
