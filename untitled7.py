import streamlit as st
import untitled5 as app1
import untitled6 as app2
import untitled10 as app3
import bcrypt
from dotenv import load_dotenv
import os

# Charger les variables d'environnement (noms d'utilisateurs, mots de passe hashés)
load_dotenv()

# Fonction pour vérifier un mot de passe
def check_password(hashed_password, password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

# Fonction pour récupérer les identifiants des utilisateurs depuis le fichier .env
def get_user_credentials():
    users = []
    for key in os.environ.keys():
        if key.endswith('_USERNAME'):
            username_key = key
            password_key = key.replace('USERNAME', 'PASSWORD_HASH')
            username = os.getenv(username_key)
            password_hash = os.getenv(password_key)
            users.append({'username': username, 'password_hash': password_hash})
    return users

# Fonction pour rediriger vers une URL avec JavaScript
def js_redirect(url):
    js_code = f"""
    <script>
      window.location.href = "{url}";
    </script>
    """
    st.write(js_code, unsafe_allow_html=True)

def main():
    # Configuration de l'application Streamlit (titre, layout)
    st.set_page_config(page_title="ATALIAN COBOT", layout="wide")

    # Styles CSS personnalisés (pour le fond noir, le texte blanc, etc.)
    st.markdown(
        """
        <style>
        .stApp {
            background-color: black;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Initialisation de l'état de la session
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = ''
    if 'selected_app' not in st.session_state:
        st.session_state['selected_app'] = None

    # Récupération des paramètres de la requête depuis l'URL
    query_params = st.query_params
    if 'logged_in' in query_params:
        st.session_state['logged_in'] = query_params['logged_in'] == 'true'
    if 'app' in query_params:
        st.session_state['selected_app'] = query_params['app']

    # Affichage de la page de connexion ou de sélection d'application en fonction de l'état de connexion
    if st.session_state['logged_in']:
        app_selection_page()
    else:
        login_section()

# Section de connexion
def login_section():
    # ... (code inchangé, affichage du formulaire de connexion, vérification des identifiants)

# Page de sélection d'application
def app_selection_page():
    # ... (code inchangé, affichage des logos, bouton de déconnexion, boutons pour sélectionner les applications)

    # Exécution de l'application sélectionnée si elle existe
    if st.session_state['selected_app']:
        run_selected_app()

# Exécution de l'application sélectionnée
def run_selected_app():
    if st.session_state['selected_app'] == "RQUARTZ - IMON":
        app1.main()
    elif st.session_state['selected_app'] == "RQUARTZ - T2F":
        app2.main()
    elif st.session_state['selected_app'] == "ECOBOT 40":
        app3.main()

if __name__ == '__main__':
    main()
