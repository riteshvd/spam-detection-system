"""
Train Naive Bayes classifier on spam data
Run: python spam_detection_service/train.py
"""
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import pickle
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_model():
    """Train and save ML model"""

    try:
        # Load data
        logger.info("Loading training data...")
        df = pd.read_csv("data/training_data.csv")
        logger.info(f"Loaded {len(df)} samples")

        X = df["text"].values
        y = df["label"].values

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Create pipeline
        logger.info("Training model...")
        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=1000, stop_words="english")),
            ("clf", MultinomialNB()),
        ])

        # Train
        pipeline.fit(X_train, y_train)

        # Evaluate
        y_pred = pipeline.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)

        logger.info(f"Accuracy: {accuracy:.2%}")
        logger.info(f"Precision: {precision:.2%}")
        logger.info(f"Recall: {recall:.2%}")

        # Save model using pickle (compatible with Flask loader)
        os.makedirs("models", exist_ok=True)
        with open("models/spam_nb.pkl", "wb") as f:
            pickle.dump(pipeline, f)
        logger.info("✓ Model saved to models/spam_nb.pkl")

        return True

    except Exception as e:
        logger.error(f"✗ Error training model: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    train_model()