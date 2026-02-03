# backend/reporting_service/app.py
"""
Reporting Service (Port 5001)
- Subscribes to Redis for classification results
- Updates daily reports in MongoDB
- Provides report API endpoint
"""
import os
from flask import Flask, jsonify
from threading import Thread
import logging
import json
import traceback

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.repositories import DailyReportRepository
from common.messaging import RedisMessaging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global variable to track listener status
listener_started = False


def start_listener():
    """
    Background task: Listen for classification results from Redis
    Update daily reports as messages arrive
    """
    global listener_started
    
    def process_message(payload):
        """Process incoming classification result"""
        try:
            classification = payload.get("classification")
            if not classification:
                logger.warning("Invalid payload: missing classification")
                return
            
            logger.info(f"Processing classification: {classification}")
            
            # Update daily report
            report = DailyReportRepository.update_daily_report(classification)
            if report:
                logger.info(f"Report updated: {report}")
            else:
                logger.error("Failed to update report")
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(traceback.format_exc())
    
    # Start listening
    logger.info("Starting Redis listener...")
    RedisMessaging.listen_for_results(process_message)


def start_background_listener():
    """Start Redis listener in background thread"""
    global listener_started
    
    if listener_started:
        logger.warning("Listener already started")
        return
    
    listener_thread = Thread(target=start_listener, daemon=True)
    listener_thread.start()
    listener_started = True
    logger.info("✓ Background listener started")


@app.before_request
def before_first_request():
    """Initialize on first request"""
    global listener_started
    if not listener_started:
        start_background_listener()


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "reporting",
        "listener_active": listener_started,
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route("/api/reports/daily", methods=["GET"])
def get_daily_report():
    """
    Get today's spam report
    Returns: {"date": "2025-12-05", "total_checked": 10, "spam_count": 7, ...}
    """
    try:
        report = DailyReportRepository.get_today_report()
        
        if not report:
            logger.error("Failed to fetch report")
            return jsonify({"error": "Failed to fetch report"}), 500
        
        logger.info(f"Returning report: {report}")
        return jsonify(report), 200
    
    except Exception as e:
        logger.error(f"Error fetching report: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/reports/stats", methods=["GET"])
def get_statistics():
    """Get basic statistics"""
    try:
        report = DailyReportRepository.get_today_report()
        return jsonify({
            "today_report": report,
            "listener_active": listener_started
        }), 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Start listener immediately
    start_background_listener()
    
    # Run Flask app
    app.run(host="0.0.0.0", port=5001, debug=False)
