import streamlit as st
import untitled5 as app1
import untitled6 as app2
import untitled10 as app3
import bcrypt
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()

# Fonction pour vérifier le mot de passe haché
def check_password(hashed_password, password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

# Fonction pour récupérer les identifiants depuis le fichier .env
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

# Fonction de connexion
def login(username, password):
    users = get_user_credentials()
    for user in users:
        if user['username'] == username:
            if check_password(user['password_hash'], password):
                return True
    return False

# Fonction principale
def main():
    st.set_page_config(page_title="ATALIAN COBOT", layout="wide")
    st.markdown(
        """
        <style>
        .stApp {
            background-color: black;
            color: white;
        }
        .custom-title {
            color: #ff6347;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    # Maintenir l'état d'authentification
    query_params = st.query_params
    if 'logout' in query_params:
        st.session_state['logged_in'] = False
        st.session_state.pop('username', None)
        st.session_state.pop('selected_app', None)
        st.query_params.clear()
        st.experimental_rerun()

    if not st.session_state['logged_in']:
        login_section()
    else:
        app_selection_page()

# Section de connexion
def login_section():
    st.title("Connexion à l'interface de visualisation ATALIAN / COBOT")
    st.markdown('<h1 class="custom-title">Connexion Interface de visualisation ATALIAN / COBOT</h1>', unsafe_allow_html=True)
    st.image("atalian-logo (1).png", width=300)  # Chemin vers votre logo

    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type='password')
    if st.button("Connexion"):
        if login(username, password):
            st.success(f"Bienvenue {username}")
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.query_params.clear()
            st.experimental_rerun()
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect")

# Page de sélection de l'application
def app_selection_page():
    st.markdown('<h1 class="custom-title">Applications RQUARTZ</h1>', unsafe_allow_html=True)

    st.markdown("### Sélectionnez une application")
    col1, col2, col3 = st.columns(3)

    if 'selected_app' not in st.session_state:
        st.session_state['selected_app'] = None

    with col1:
        if st.button("RQUARTZ - IMON"):
            st.session_state['selected_app'] = "RQUARTZ - IMON"
            st.experimental_rerun()

    with col2:
        if st.button("RQUARTZ - T2F"):
            st.session_state['selected_app'] = "RQUARTZ - T2F"
            st.experimental_rerun()
            
    with col3:
        if st.button("ECOBOT 40"):
            st.session_state['selected_app'] = "ECOBOT 40"
            st.experimental_rerun()

    if st.session_state['selected_app']:
        run_selected_app()
    
    if st.button("Déconnexion"):
        st.query_params.update({"logout": "true"})
        st.experimental_rerun()

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
