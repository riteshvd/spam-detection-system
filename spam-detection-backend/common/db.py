import os
import logging
from pymongo import MongoClient
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/spam-detection")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_CHANNEL = os.getenv("REDIS_CHANNEL", "spam-detection-results")

try:
    mongo_client = MongoClient(MONGODB_URL)
    mongo_client.admin.command('ping')
    db = mongo_client["spam-detection"]
    logger.info("✓ MongoDB connected")
except Exception as e:
    logger.error(f"✗ MongoDB failed: {e}")
    db = None

try:
    redis_client = redis.from_url(REDIS_URL)
    redis_client.ping()
    logger.info("✓ Redis connected")
except Exception as e:
    logger.error(f"✗ Redis failed: {e}")
    redis_client = None

def get_db():
    return db

def get_redis():
    return redis_client
