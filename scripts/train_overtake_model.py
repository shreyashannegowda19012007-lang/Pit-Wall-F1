import os
import numpy as np
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

def train_overtake_model():
    print("Generating synthetic F1 overtake training data...")
    # Features: delta_pace_s, tyre_age_delta, drs_active (0/1), track_overtake_difficulty (0-1)
    np.random.seed(42)
    n_samples = 5000
    
    delta_pace_s = np.random.normal(loc=0.5, scale=1.5, size=n_samples) # Negative means attacking car is faster
    tyre_age_delta = np.random.randint(-15, 15, size=n_samples) # Negative means attacking car has newer tyres
    drs_active = np.random.choice([0, 1], size=n_samples, p=[0.3, 0.7])
    track_diff = np.random.uniform(0.1, 0.9, size=n_samples)
    
    # Probability of overtake
    # Base probability
    logits = -1.0 - (delta_pace_s * 2.5) - (tyre_age_delta * 0.1) + (drs_active * 2.0) - (track_diff * 1.5)
    
    probs = 1.0 / (1.0 + np.exp(-logits))
    
    y = np.random.binomial(1, probs)
    
    X = pd.DataFrame({
        'delta_pace_s': delta_pace_s,
        'tyre_age_delta': tyre_age_delta,
        'drs_active': drs_active,
        'track_overtake_difficulty': track_diff
    })
    
    print("Training RandomForestClassifier...")
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42))
    ])
    
    pipeline.fit(X, y)
    
    acc = pipeline.score(X, y)
    print(f"Model trained. Accuracy on synthetic data: {acc:.2f}")
    
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'models', 'overtake_probability')
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, 'model.pkl')
    
    with open(model_path, 'wb') as f:
        pickle.dump(pipeline, f)
        
    print(f"Model saved successfully to {model_path}")

if __name__ == "__main__":
    train_overtake_model()
