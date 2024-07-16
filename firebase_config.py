import firebase_admin
from firebase_admin import credentials, firestore

def init_firebase():
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate('cobotata-7f514-firebase-adminsdk-h224s-04fee79562.json')  # Remplacez par le chemin de votre fichier de clé de service
            firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase: {e}")

init_firebase()

db = firestore.client()
