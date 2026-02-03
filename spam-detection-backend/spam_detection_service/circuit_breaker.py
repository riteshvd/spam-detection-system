# spam_detection_service/circuit_breaker.py
"""
Circuit Breaker Pattern Implementation
Prevents cascading failures in distributed system
"""

from pybreaker import CircuitBreaker
import logging

logger = logging.getLogger(__name__)

# ===== CIRCUIT BREAKERS =====

# Circuit breaker for ML model predictions
ml_circuit_breaker = CircuitBreaker(
    fail_max=5,              # Open circuit after 5 failures
    reset_timeout=60,        # Try again after 60 seconds
    name="ML_Prediction"
)

# Circuit breaker for database operations
db_circuit_breaker = CircuitBreaker(
    fail_max=3,              # Open circuit after 3 failures
    reset_timeout=30,        # Try again after 30 seconds
    name="Database"
)

# Circuit breaker for external API calls
api_circuit_breaker = CircuitBreaker(
    fail_max=4,
    reset_timeout=45,
    name="External_API"
)

def get_circuit_breaker_status(breaker):
    """Get safe status from circuit breaker"""
    return {
        "state": str(getattr(breaker, 'state', 'unknown')),
        "is_open": getattr(breaker, 'opened', False),
        "failure_count": getattr(breaker, 'fail_counter', 0),
        "reset_timeout": getattr(breaker, 'reset_timeout', 0),
        "name": getattr(breaker, 'name', 'unknown')
    }

def get_all_breakers_status():
    """Get status of all circuit breakers"""
    return {
        "ml_prediction_breaker": get_circuit_breaker_status(ml_circuit_breaker),
        "db_breaker": get_circuit_breaker_status(db_circuit_breaker),
        "api_breaker": get_circuit_breaker_status(api_circuit_breaker)
    }
