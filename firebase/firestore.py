import firebase_admin
from firebase_admin import credentials, firestore, storage
import os

if not firebase_admin._apps:
    cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS", "firebase_key.json"))
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET", "")
    })
db = firestore.client()


def save_signal(user_id, signal, annotated_path, caption):
    doc_ref = db.collection("signals").document()
    doc_ref.set({
        "user_id": user_id,
        "signal": signal,
        "annotated_chart": annotated_path,
        "caption": caption
    })
    return {"status": "ok"}

def get_user_signals(user_id):
    signals = db.collection("signals").where("user_id", "==", user_id).stream()
    return [s.to_dict() for s in signals]

def save_feedback(user_id, signal_id, rating, comment):
    doc_ref = db.collection("feedback").document()
    doc_ref.set({
        "user_id": user_id,
        "signal_id": signal_id,
        "rating": rating,
        "comment": comment
    })
    return {"status": "ok"} 