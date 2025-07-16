FROM python:3.11-slim-buster

WORKDIR /app/ML

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY chat.py .
COPY geo_recommender.py .
COPY rescheduler.py .
COPY ml_api.py .

EXPOSE 8001

CMD ["uvicorn", "ml_api:app", "--host", "0.0.0.0", "--port", "8001"]
