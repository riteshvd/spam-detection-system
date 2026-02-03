# backend/spam_detection_service/preprocessor.py
import re
import string

def preprocess_email(text: str) -> str:
    """
    Clean and normalize email text for ML
    """
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|ftp\S+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove special characters (keep spaces)
    text = re.sub(f'[{re.escape(string.punctuation)}0-9]', ' ', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text
