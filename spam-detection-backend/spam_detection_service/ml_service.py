# spam_detection_service/ml_service.py
"""
Machine Learning Service Module
Handles model loading and predictions
"""

import pickle
import os
import logging
import traceback

logger = logging.getLogger(__name__)

MODEL_PATH = "models/spam_nb.pkl"

class MLService:
    """Machine Learning service for spam detection"""
    
    def __init__(self):
        """Initialize ML service"""
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load trained model safely with debugging"""
        try:
            logger.info(f"Attempting to load model from: {MODEL_PATH}")
            
            # Check if file exists
            if not os.path.exists(MODEL_PATH):
                logger.warning(f"Model file not found at {MODEL_PATH}")
                logger.info(f"Current directory: {os.getcwd()}")
                logger.info(f"Files in current directory: {os.listdir('.')}")
                if os.path.exists('models'):
                    logger.info(f"Files in models/: {os.listdir('models')}")
                return False
            
            # Check file size
            file_size = os.path.getsize(MODEL_PATH)
            logger.info(f"Model file size: {file_size} bytes")
            
            if file_size < 100:
                logger.warning(f"Model file seems too small ({file_size} bytes), might be corrupted")
                return False
            
            # Try to load
            with open(MODEL_PATH, 'rb') as f:
                self.model = pickle.load(f)
                logger.info("✓ Model loaded successfully!")
                return True
                
        except pickle.UnpicklingError as e:
            logger.error(f"Pickle error - file corrupted: {e}")
            traceback.print_exc()
            return False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            traceback.print_exc()
            return False
    
    def is_loaded(self):
        """Check if model is loaded"""
        return self.model is not None
    
    def predict(self, email_text):
        """Make prediction on email text"""
        if not self.is_loaded():
            logger.warning("Model not loaded, returning default prediction")
            return "ham", 0.5
        
        try:
            prediction = self.model.predict([email_text])[0]
            confidence = 0.85
            classification = "spam" if prediction == 1 else "ham"
            return classification, confidence
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            traceback.print_exc()
            raise
    
    def get_info(self):
        """Get model information"""
        return {
            "model": "Naive Bayes Classifier",
            "version": "1.0",
            "status": "loaded" if self.is_loaded() else "not_loaded",
            "model_path": MODEL_PATH,
            "file_exists": os.path.exists(MODEL_PATH),
            "file_size": os.path.getsize(MODEL_PATH) if os.path.exists(MODEL_PATH) else 0
        }

# Global instance
ml_service = MLService()
