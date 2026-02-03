# backend/test_backend.py
"""
Test both services are working
Run: python test_backend.py
"""
import requests
import time
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_services():
    """Test both services"""
    
    # Wait for services to start
    time.sleep(3)
    
    # Test 1: Health checks
    logger.info("\n=== Testing Health Checks ===")
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        logger.info(f"Spam Service: {response.json()}")
    except Exception as e:
        logger.error(f"Spam Service health check failed: {e}")
    
    try:
        response = requests.get("http://localhost:5001/health", timeout=5)
        logger.info(f"Reporting Service: {response.json()}")
    except Exception as e:
        logger.error(f"Reporting Service health check failed: {e}")
    
    # Test 2: Model info
    logger.info("\n=== Testing Model Info ===")
    try:
        response = requests.get("http://localhost:5000/api/ml/model-info")
        logger.info(f"Model Info: {response.json()}")
    except Exception as e:
        logger.error(f"Model info failed: {e}")
    
    # Test 3: Prediction
    logger.info("\n=== Testing Prediction ===")
    test_emails = [
        ("Click here to win free money now!", "spam"),
        ("Hello, how are you doing?", "ham"),
        ("Congratulations you won $1000!", "spam"),
        ("See you at the meeting tomorrow", "ham"),
    ]
    
    for email, expected in test_emails:
        try:
            response = requests.post(
                "http://localhost:5000/api/ml/predict",
                json={"email_text": email},
                timeout=10
            )
            result = response.json()
            classification = result.get("classification")
            confidence = result.get("confidence", 0)
            
            match = "✓" if classification == expected else "✗"
            logger.info(f"{match} '{email[:30]}...' → {classification} ({confidence:.2%})")
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
    
    # Test 4: Daily report
    logger.info("\n=== Testing Daily Report ===")
    time.sleep(2)  # Wait for async updates
    try:
        response = requests.get("http://localhost:5001/api/reports/daily")
        report = response.json()
        logger.info(f"Report: {json.dumps(report, indent=2)}")
    except Exception as e:
        logger.error(f"Report fetch failed: {e}")

if __name__ == "__main__":
    test_services()
