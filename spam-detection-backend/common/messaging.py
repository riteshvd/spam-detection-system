import json
import logging
from .db import get_redis, REDIS_CHANNEL

logger = logging.getLogger(__name__)

class RedisMessaging:
    @staticmethod
    def publish_result(payload: dict) -> bool:
        redis = get_redis()
        if not redis:
            logger.error("Redis not available")
            return False
        try:
            message = json.dumps(payload)
            redis.publish(REDIS_CHANNEL, message)
            logger.info(f"✓ Published: {payload}")
            return True
        except Exception as e:
            logger.error(f"✗ Error: {e}")
            return False

    @staticmethod
    def subscribe_results():
        redis = get_redis()
        if not redis:
            return None
        try:
            pubsub = redis.pubsub()
            pubsub.subscribe(REDIS_CHANNEL)
            logger.info(f"✓ Subscribed to {REDIS_CHANNEL}")
            return pubsub
        except Exception as e:
            logger.error(f"✗ Error: {e}")
            return None

    @staticmethod
    def listen_for_results(callback):
        pubsub = RedisMessaging.subscribe_results()
        if not pubsub:
            return
        logger.info("Starting listener...")
        for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                payload = json.loads(message["data"])
                logger.info(f"Message received: {payload}")
                callback(payload)
            except Exception as e:
                logger.error(f"✗ Error: {e}")
