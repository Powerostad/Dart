FROM python:3.8-slim

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

RUN echo "[global]" > /etc/pip.conf && \
    echo "index-url = https://mirror-pypi.runflare.com/simple" >> /etc/pip.conf
# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

RUN python manage.py set_collation
RUN python manage.py initiate_plans

CMD ["gunicorn", "tradeproject.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
