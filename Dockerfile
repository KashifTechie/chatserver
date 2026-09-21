# 1. Base image (Python environment)
FROM python:3.10-slim

# 2. Set working directory
WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3. Copy requirements first (for caching)
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy project code
COPY . .

# 6. Run Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
