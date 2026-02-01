"""
Script to train the triage model on symptom data.
"""

import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Sample training data
TRAINING_DATA = [
    # (symptoms, severity)
    ("chest pain difficulty breathing", 5),
    ("severe chest pressure shortness of breath", 5),
    ("unconscious not responding", 5),
    ("severe bleeding cannot stop", 5),
    
    ("high fever 103 degrees chills", 4),
    ("severe abdominal pain vomiting", 4),
    ("broken arm visible deformity", 4),
    ("deep cut bleeding heavily", 4),
    
    ("fever cough sore throat", 3),
    ("ear pain infection", 3),
    ("moderate back pain", 3),
    ("rash spreading itching", 3),
    
    ("cold runny nose sneezing", 2),
    ("mild headache tired", 2),
    ("minor muscle ache", 2),
    ("slight nausea", 2),
    
    ("prescription refill needed", 1),
    ("annual checkup routine", 1),
    ("follow up appointment", 1),
    ("vaccination request", 1),
]


def train_model():
    """Train and save the triage model."""
    X_text = [item[0] for item in TRAINING_DATA]
    y = [item[1] for item in TRAINING_DATA]
    
    # Vectorize text
    vectorizer = TfidfVectorizer(max_features=500)
    X = vectorizer.fit_transform(X_text)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train classifier
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    predictions = model.predict(X_test)
    print("Model Performance:")
    print(classification_report(y_test, predictions))
    
    # Save model and vectorizer
    with open("../models/trained/triage_model.pkl", "wb") as f:
        pickle.dump({"model": model, "vectorizer": vectorizer}, f)
    
    print("Model saved to models/trained/triage_model.pkl")


if __name__ == "__main__":
    train_model()
