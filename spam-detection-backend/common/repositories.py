from datetime import datetime
from bson import ObjectId
from .db import get_db
import logging

logger = logging.getLogger(__name__)

class SubmissionRepository:
    @staticmethod
    def insert_submission(email_text: str) -> str:
        db = get_db()
        if not db:
            return None
        try:
            doc = {"email_text": email_text, "submitted_at": datetime.utcnow()}
            result = db.spam_submissions.insert_one(doc)
            logger.info(f"✓ Submission saved: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"✗ Error: {e}")
            return None

class ClassificationRepository:
    @staticmethod
    def insert_classification(submission_id: str, classification: str, confidence: float) -> bool:
        db = get_db()
        if not db:
            return False
        if classification not in ["spam", "ham"]:
            return False
        try:
            doc = {
                "submission_id": ObjectId(submission_id) if submission_id else None,
                "classification": classification,
                "confidence": float(confidence),
                "created_at": datetime.utcnow()
            }
            db.classification_results.insert_one(doc)
            logger.info(f"✓ Classification saved")
            return True
        except Exception as e:
            logger.error(f"✗ Error: {e}")
            return False

class DailyReportRepository:
    @staticmethod
    def update_daily_report(classification: str) -> dict:
        db = get_db()
        if not db:
            return None
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            report = db.daily_reports.find_one({"date": today})
            if not report:
                report = {
                    "date": today,
                    "total_checked": 0,
                    "spam_count": 0,
                    "ham_count": 0,
                    "spam_percentage": 0.0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            report["total_checked"] += 1
            if classification == "spam":
                report["spam_count"] += 1
            elif classification == "ham":
                report["ham_count"] += 1
            total = report["total_checked"]
            if total > 0:
                report["spam_percentage"] = round((report["spam_count"] / total) * 100, 2)
            else:
                report["spam_percentage"] = 0.0
            report["updated_at"] = datetime.utcnow()
            db.daily_reports.replace_one({"date": today}, report, upsert=True)
            logger.info(f"✓ Report updated: {report}")
            return report
        except Exception as e:
            logger.error(f"✗ Error: {e}")
            return None

    @staticmethod
    def get_today_report() -> dict:
        db = get_db()
        if not db:
            return None
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            report = db.daily_reports.find_one({"date": today})
            if not report:
                return {
                    "date": today,
                    "total_checked": 0,
                    "spam_count": 0,
                    "ham_count": 0,
                    "spam_percentage": 0.0
                }
            if "_id" in report:
                del report["_id"]
            return report
        except Exception as e:
            logger.error(f"✗ Error: {e}")
            return None
