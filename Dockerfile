FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies and MySQL client
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        pkg-config \
        default-libmysqlclient-dev \
        python3-dev \
        build-essential \
        gcc \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

CMD ["python", "manage.py", "runserver" ,"0.0.0.0:8000"]
