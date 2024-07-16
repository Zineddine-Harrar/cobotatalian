from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import credentials, firestore

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

def init_firebase():
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate('GOOGLE_APPLICATION_CREDENTIALS')  # Remplacez par le chemin de votre fichier de clé de service
            firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase: {e}")

init_firebase()

db = firestore.client()
