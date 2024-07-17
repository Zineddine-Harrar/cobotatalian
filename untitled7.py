import streamlit as st
import untitled5 as app1
import untitled6 as app2
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
    st.set_page_config(page_title="Simple Auth App", layout="wide")

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        login_section()
    else:
        if 'selected_app' in st.session_state:
            run_selected_app()
        else:
            app_selection_page()

# Section de connexion
def login_section():
    st.title("Connexion")
    st.image("atalian-logo (1).png", width=300)  # Chemin vers votre logo

    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type='password')
    if st.button("Connexion"):
        if login(username, password):
            st.success(f"Bienvenue {username}")
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.experimental_rerun()
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect")

# Page de sélection de l'application
def app_selection_page():
    st.title("Applications RQUARTZ")

    st.markdown("### Sélectionnez une application")
    col1, col2, col3 = st.columns(3)

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

    if st.button("Deconnexion"):
        st.session_state['logged_in'] = False
        st.session_state.pop('username', None)
        st.session_state.pop('selected_app', None)
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
