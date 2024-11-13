FROM python:3.10-slim

WORKDIR /app/backend 

COPY ../requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ../backend /app
COPY ../.env ./

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
