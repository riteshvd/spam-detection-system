# spam_detection_service/app.py
"""
Email Spam Detection Flask API
Distributed System with JWT Auth & Circuit Breaker
"""

from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import logging
import traceback

# Import custom modules
from .circuit_breaker import ml_circuit_breaker, get_all_breakers_status
from .auth import JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES, validate_credentials, log_auth_attempt
from .ml_service import ml_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== FLASK APP SETUP =====
app = Flask(__name__)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_ACCESS_TOKEN_EXPIRES
jwt = JWTManager(app)

# Log startup
logger.info("=" * 50)
logger.info("FLASK APP STARTING")
logger.info("=" * 50)
logger.info(f"Model status: {'LOADED' if ml_service.is_loaded() else 'NOT LOADED'}")
logger.info("=" * 50)

# ===== AUTHENTICATION ENDPOINTS =====

@app.route('/auth/login', methods=['POST'])
def login():
    """Login endpoint to get JWT token"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({"error": "Missing username or password"}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if validate_credentials(username, password):
            access_token = create_access_token(identity=username)
            log_auth_attempt(username, True)
            return jsonify({
                "access_token": access_token,
                "username": username,
                "expires_in": "24 hours"
            }), 200
        else:
            log_auth_attempt(username, False)
            return jsonify({"error": "Invalid credentials"}), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Authentication failed"}), 500

@app.route('/auth/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """Verify JWT token validity"""
    try:
        current_user = get_jwt_identity()
        return jsonify({
            "status": "valid",
            "user": current_user
        }), 200
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return jsonify({"error": "Token verification failed"}), 401

# ===== HEALTH CHECK ENDPOINTS =====

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "spam-detection",
        "model_loaded": ml_service.is_loaded()
    }), 200

@app.route('/api/ml/model-info', methods=['GET'])
@jwt_required()
def model_info():
    """Get model information"""
    return jsonify(ml_service.get_info()), 200

# ===== ML PREDICTION ENDPOINT =====

@app.route('/api/ml/predict', methods=['POST'])
@jwt_required()
def predict():
    """Predict if email is spam or ham with Circuit Breaker protection"""
    try:
        current_user = get_jwt_identity()
        data = request.json
        
        if not data or 'email_text' not in data:
            return jsonify({"error": "Missing email_text field"}), 400
        
        email_text = data.get('email_text', '')
        
        if not email_text:
            return jsonify({"error": "email_text cannot be empty"}), 400
        
        # Make prediction with circuit breaker
        try:
            @ml_circuit_breaker
            def make_prediction():
                """Wrapped prediction function for circuit breaker"""
                return ml_service.predict(email_text)
            
            classification, confidence = make_prediction()
            
            logger.info(f"User {current_user} - Prediction: {classification} (confidence: {confidence})")
            
            return jsonify({
                "email_text": email_text[:50],
                "classification": classification,
                "confidence": confidence,
                "user": current_user
            }), 200
            
        except Exception as circuit_error:
            logger.error(f"Circuit breaker triggered or prediction error: {circuit_error}")
            
            if ml_circuit_breaker.opened:
                logger.warning("ML Circuit Breaker is OPEN - service temporarily unavailable")
                return jsonify({
                    "error": "Prediction service temporarily unavailable",
                    "retry_after": 60,
                    "circuit_breaker_status": "OPEN"
                }), 503
            else:
                logger.error(f"Prediction error: {circuit_error}")
                traceback.print_exc()
                return jsonify({
                    "error": "Prediction failed",
                    "circuit_breaker_status": str(ml_circuit_breaker.state)
                }), 500
            
    except Exception as e:
        logger.error(f"Request error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Request processing failed"}), 500

# ===== CIRCUIT BREAKER STATUS ENDPOINT =====

@app.route('/api/ml/circuit-breaker-status', methods=['GET'])
@jwt_required()
def circuit_breaker_status():
    """Get circuit breaker status"""
    try:
        return jsonify(get_all_breakers_status()), 200
    except Exception as e:
        logger.error(f"Circuit breaker status error: {e}")
        traceback.print_exc()
        return jsonify({
            "error": "Failed to get circuit breaker status",
            "details": str(e)
        }), 500

# ===== SYSTEM STATUS ENDPOINT =====

@app.route('/api/ml/status', methods=['GET'])
@jwt_required()
def status():
    """Get full system status"""
    return jsonify({
        "backend": "running",
        "model": "loaded" if ml_service.is_loaded() else "not_loaded",
        "database": "connected",
        "circuit_breaker_ml": str(ml_circuit_breaker.state),
        "timestamp": str(__import__('datetime').datetime.now()),
        "authenticated_user": get_jwt_identity()
    }), 200

# ===== ERROR HANDLERS =====

@app.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized access"""
    return jsonify({"error": "Missing or invalid authentication token"}), 401

@app.errorhandler(403)
def forbidden(error):
    """Handle forbidden access"""
    return jsonify({"error": "Access forbidden"}), 403

@app.errorhandler(404)
def not_found(error):
    """Handle not found"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server error"""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info("Starting Flask app with JWT Authentication and Circuit Breaker...")
    app.run(host='0.0.0.0', port=5000, debug=False)