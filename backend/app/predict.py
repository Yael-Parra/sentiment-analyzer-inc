from .model import model, vectorizer

def predict_hate(comment: str):
    vector = vectorizer.transform([comment])
    pred = model.predict(vector)[0]
    prob = model.predict_proba(vector)[0][1]  # probabilidad de ser hate
    return bool(pred), float(prob)
