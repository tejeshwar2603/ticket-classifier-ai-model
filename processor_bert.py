import csv
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

try:
    from sentence_transformers import SentenceTransformer
    _has_bert = True
except Exception:
    _has_bert = False

model_name = 'all-MiniLM-L6-v2'
model_embedding = SentenceTransformer(model_name) if _has_bert else None
classifier_path = Path(__file__).with_name('bert_classifier.joblib')
encoder_path = Path(__file__).with_name('label_encoder.joblib')
vectorizer_path = Path(__file__).with_name('vectorizer.joblib')
training_data_path = Path(__file__).parent / 'data' / 'logs.csv'
vectorizer = None


def load_training_data(path):
    logs = []
    labels = []
    if not path.exists():
        return logs, labels
    with path.open(newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            log = row.get('log') or row.get('message') or ''
            label = row.get('label') or ''
            if log and label:
                logs.append(log)
                labels.append(label)
    return logs, labels


def train_classifier():
    global vectorizer
    logs, labels = load_training_data(training_data_path)
    if not logs:
        raise FileNotFoundError(
            f"Training data not found at {training_data_path}. "
            "Create a CSV file with columns: log,label"
        )
    encoder = LabelEncoder()
    y = encoder.fit_transform(labels)
    if _has_bert:
        embeddings = model_embedding.encode(logs)
    else:
        vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        embeddings = vectorizer.fit_transform(logs)
        joblib.dump(vectorizer, vectorizer_path)
    classifier = LogisticRegression(max_iter=500)
    classifier.fit(embeddings, y)
    joblib.dump(classifier, classifier_path)
    joblib.dump(encoder, encoder_path)
    return classifier, encoder


def load_classifier():
    global vectorizer
    if classifier_path.exists() and encoder_path.exists():
        classifier = joblib.load(classifier_path)
        encoder = joblib.load(encoder_path)
        if not _has_bert and vectorizer_path.exists():
            vectorizer = joblib.load(vectorizer_path)
        return classifier, encoder
    return train_classifier()


classifier, label_encoder = load_classifier()


def classify_with_bert(log_message):
    if _has_bert:
        embedding = model_embedding.encode([log_message])
    else:
        if vectorizer is None:
            raise RuntimeError("TF-IDF vectorizer is not initialized.")
        embedding = vectorizer.transform([log_message])
    probabilities = classifier.predict_proba(embedding)[0]
    if max(probabilities) < 0.5:
        return "Unclassified"
    predicted_index = classifier.predict(embedding)[0]
    return label_encoder.inverse_transform([predicted_index])[0]


if __name__ == "__main__":
    logs = [
        "alpha.osapi_compute.wsgi.server - 12.10.11.1 - API returned 404 not found error",
        "GET /v2/3454/servers/detail HTTP/1.1 RCODE   404 len: 1583 time: 0.1878400",
        "System crashed due to drivers errors when restarting the server",
        "Hey bro, chill ya!",
        "Multiple login failures occurred on user 6454 account",
        "Server A790 was restarted unexpectedly during the process of data transfer",
    ]
    for log in logs:
        label = classify_with_bert(log)
        print(f"Log: {log}")
        print(f"Classified as: {label}")