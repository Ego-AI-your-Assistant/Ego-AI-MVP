FROM python:3.11-slim-buster

WORKDIR /app/ML

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make startup script executable
RUN chmod +x start_services.sh

EXPOSE 8001 8002 8003

CMD ["./start_services.sh"]