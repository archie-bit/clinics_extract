FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set the working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium browser
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy the rest of the application code
COPY . .
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "scripts/scrapper.py"]