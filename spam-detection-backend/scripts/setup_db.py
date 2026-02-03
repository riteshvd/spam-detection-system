import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.db import get_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_mongodb():
    db = get_db()
    if db is None:
        logger.error("Cannot connect to MongoDB")
        return False
    try:
        if "spam_submissions" not in db.list_collection_names():
            db.create_collection("spam_submissions")
            logger.info("✓ Created spam_submissions")
        db.spam_submissions.create_index("submitted_at")

        if "classification_results" not in db.list_collection_names():
            db.create_collection("classification_results")
            logger.info("✓ Created classification_results")
        db.classification_results.create_index("created_at")
        db.classification_results.create_index("submission_id")

        if "daily_reports" not in db.list_collection_names():
            db.create_collection("daily_reports")
            logger.info("✓ Created daily_reports")
        db.daily_reports.create_index("date", unique=True)

        logger.info("\n✓ Database setup complete!")
        return True
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    setup_mongodb()
