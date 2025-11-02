"""
Sleep Score Prediction Model
Trains on sleep data and predicts optimal sunrise settings
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib
import re

MODEL_PATH = "sleep_model.pkl"

def parse_duration(text):
    """converts hours into minutes"""
    if pd.isna(text):
        return np.nan
    match = re.match(r"(\d+)h\s*(\d+)?min?", str(text))
    if not match:
        return np.nan
    hours = int(match.group(1))
    minutes = int(match.group(2)) if match.group(2) else 0
    return hours * 60 + minutes

def load_and_clean_data(path="sleep_data.csv"):
    """Load and preprocess sleep data from CSV"""
    df = pd.read_csv(path)
    
    print(f"Raw data loaded: {len(df)} rows")
    
    # Keep only rows with valid sleep score and duration
    df = df.dropna(subset=["Avg Score", "Avg Duration"])
    print(f"After removing invalid scores: {len(df)} rows")

    # Parse duration strings
    df["Avg Duration (min)"] = df["Avg Duration"].apply(parse_duration)
    
    # Handle missing Sleep Need - use duration as fallback
    df["Avg Sleep Need (min)"] = df["Avg Sleep Need"].apply(parse_duration)
    df["Avg Sleep Need (min)"] = df["Avg Sleep Need (min)"].fillna(df["Avg Duration (min)"])
    
    # Parse time strings - handle HH:MM format
    def parse_hour(time_str):
        if pd.isna(time_str):
            return np.nan
        try:
            if ':' in str(time_str):
                hour = int(str(time_str).split(':')[0])
                return hour
            return np.nan
        except:
            return np.nan
    
    df["Bedtime (h)"] = df["Avg Bedtime"].apply(parse_hour)
    df["Wake Time (h)"] = df["Avg Wake Time"].apply(parse_hour)

    # Remove rows with any NaN values in required columns
    required_cols = ["Avg Score", "Avg Duration (min)", "Avg Sleep Need (min)", "Bedtime (h)", "Wake Time (h)"]
    df = df.dropna(subset=required_cols)
    print(f"After cleaning: {len(df)} rows remain")
    
    if len(df) == 0:
        print("WARNING: No valid data after cleaning!")
        print("Check your sleep_data.csv file format")
        raise ValueError("No valid training data available")

    X = df[required_cols]
    y = df["Avg Score"].astype(float)

    return X, y

def train_model():
    """Train RandomForest model on sleep data"""
    X, y = load_and_clean_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=150, random_state=42)
    model.fit(X_train, y_train)

    joblib.dump(model, MODEL_PATH)
    print(f"Model trained and saved to {MODEL_PATH}")
    print(f"R² Score: {model.score(X_test, y_test):.2f}")
    print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")

def predict_brightness(date_str=None):
    """
    Predict optimal sunrise settings based on recent sleep data
    Returns: (r, g, b, duration_seconds)
    """
    model = joblib.load(MODEL_PATH)
    X, y = load_and_clean_data()

    # Use most recent data for prediction
    latest = X.iloc[-1:].to_numpy()
    pred = model.predict(latest)[0]

    # Clamp prediction between 50 and 90
    pred = np.clip(pred, 50, 90)

    # Map score (50-90) → LED brightness
    brightness = int(np.interp(pred, [50, 90], [120, 255]))

    # ----- FOR DEMO: override duration to 10 seconds -----
    duration_seconds = 10

    print(f"Predicted Sleep Score: {pred:.1f}")
    print(f"Recommended Brightness: {brightness}/255")
    print(f"Sunrise Duration (demo): {duration_seconds} seconds")

    # Warm sunrise color (orange/yellow tint)
    r = brightness
    g = int(brightness * 0.7)
    b = int(brightness * 0.2)

    return r, g, b, duration_seconds



if __name__ == "__main__":
    # Test the model functions
    print("Testing model.py...\n")
    
    try:
        print("Loading data...")
        X, y = load_and_clean_data()
        print(f"Loaded {len(X)} samples\n")
        
        print("Training model...")
        train_model()
        print()
        
        print("Making prediction...")
        r, g, b, duration = predict_brightness()
        print(f"\nRGB: ({r}, {g}, {b})")
        print(f"Duration: {duration}s")
        
    except Exception as e:
        print(f"Error: {e}")
