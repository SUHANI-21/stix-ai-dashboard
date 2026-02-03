from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier

# Demo training data
texts = [
    "ransomware command and control server",
    "phishing email campaign targeting users",
    "benign network traffic",
    "botnet malware detected in infrastructure"
]

labels = ["malware", "phishing", "benign", "botnet"]

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

model = RandomForestClassifier()
model.fit(X, labels)

def classify_threat(description):
    X_test = vectorizer.transform([description])
    prediction = model.predict(X_test)[0]
    probability = max(model.predict_proba(X_test)[0])
    return prediction, round(probability * 100, 2)
