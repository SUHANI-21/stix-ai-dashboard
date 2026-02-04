import joblib
import numpy as np
import os


class TechniquePredictor:

    def __init__(self, model_path=None, lb_path=None):
        # Allow configurable paths, but provide a safe fallback if models are missing
        model_path = model_path or os.path.join("modules", "models", "malware_classifier_lr.pkl")
        lb_path = lb_path or os.path.join("modules", "models", "label_binarizer.pkl")

        self.model = None
        self.mlb = None

        try:
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
        except Exception:
            self.model = None

        try:
            if os.path.exists(lb_path):
                self.mlb = joblib.load(lb_path)
        except Exception:
            self.mlb = None


    def predict(self, text, threshold=0.4):
        # If model not available or text is None/empty, return empty prediction
        if not self.model or not self.mlb or not text:
            return [], [0.0]

        probs = self.model.predict_proba([text])[0]

        labels = []

        for i, p in enumerate(probs):
            if p >= threshold:
                labels.append(self.mlb.classes_[i])

        return labels, probs
