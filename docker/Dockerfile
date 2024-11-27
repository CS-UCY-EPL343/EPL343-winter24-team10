FROM mariadb:latest AS mariadb

ENV MARIADB_ROOT_PASSWORD=rootpassword \
    MARIADB_DATABASE=mydatabase \
    MARIADB_USER=myuser \
    MARIADB_PASSWORD=mypassword

EXPOSE 3306

FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y \
    mariadb-client \
    libmariadb-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

COPY ../requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ../backend /app

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
