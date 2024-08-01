FROM python:3.12-alpine

WORKDIR /app

# Set environment variables to prevent Python from writing .pyc files and buffering output
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy action code
COPY action.py .

ENTRYPOINT ["python", "/app/action.py"]
