FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000 5001
ENV FLASK_ENV=production
ENV MONGODB_URL=mongodb://mongo:27017/spam-detection
ENV REDIS_URL=redis://redis:6379
CMD ["sh", "-c", "python scripts/setup_db.py && python spam_detection_service/train.py && python -m flask --app spam_detection_service.app run --host=0.0.0.0 --port=5000"]