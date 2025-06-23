import numpy as np
import joblib

class SignalEngine:
    def __init__(self, model_path):
        self.model = joblib.load(model_path)

    def predict_signal(self, features):
        proba = self.model.predict_proba([features])[0]
        signal = np.argmax(proba)
        confidence = proba[signal] * 100
        return signal, confidence  # 0: Hold, 1: Buy, 2: Sell