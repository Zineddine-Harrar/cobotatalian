import streamlit as st
from datetime import datetime, timedelta
from firebase_config import db, init_firebase
import untitled5 as app1
import untitled6 as app2
import bcrypt

# Initialiser Firebase
init_firebase()

SESSION_TIMEOUT_MINUTES = 15

def check_password(hashed_password, password):
    """Vérifier un mot de passe hashé."""
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

def login(username, password):
    try:
        user_ref = db.collection('users').document(username)
        print(f"Accessing document at path: users/{username}")
        user = user_ref.get()
        if user.exists:
            user_data = user.to_dict()
            print(f"User data retrieved: {user_data}")
            if check_password(user_data['password'], password):
                print("Login successful.")
                return True
            else:
                print("Incorrect password.")
                return False
        else:
            print("User does not exist.")
            return False
    except Exception as e:
        st.error(f"Login error: {e}")
        return False

def check_session_timeout():
    if 'last_interaction' in st.session_state:
        now = datetime.now()
        last_interaction = st.session_state['last_interaction']
        if (now - last_interaction).total_seconds() > SESSION_TIMEOUT_MINUTES * 60:
            st.warning("Session expirée en raison d'inactivité. Veuillez vous reconnecter.")
            st.session_state['logged_in'] = False
            st.session_state.pop('last_interaction', None)
            st.session_state.pop('selected_app', None)
            st.experimental_rerun()
    st.session_state['last_interaction'] = datetime.now()

def main():
    st.set_page_config(page_title="RQUARTZ Applications", layout="wide")

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        check_session_timeout()

    if not st.session_state['logged_in']:
        login_section()
    elif 'selected_app' not in st.session_state:
        app_selection_page()
    else:
        run_selected_app()

def login_section():
    logo_path = "atalian-logo (1).png"  # Changez ce chemin pour pointer vers votre logo
    st.image(logo_path, width=300)

    st.title("Système d'authentification - ATALIAN")
    st.subheader("Connexion")
    
    

    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type='password')
    if st.button("Connexion"):
        if login(username, password):
            st.success(f"Logged In as {username}")
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.session_state['last_interaction'] = datetime.now()
            st.experimental_rerun()  # Recharger la page pour montrer l'écran de sélection d'application
        else:
            st.warning("Incorrect Username/Password")

def app_selection_page():
    st.title("Applications RQUARTZ")

    st.markdown("### Sélectionnez une application")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("RQUARTZ - IMON"):
            st.session_state['selected_app'] = "RQUARTZ - IMON"
            st.experimental_rerun()

    with col2:
        if st.button("RQUARTZ - T2F"):
            st.session_state['selected_app'] = "RQUARTZ - T2F"
            st.experimental_rerun()

    if st.button("Deconnexion"):
        st.session_state['logged_in'] = False
        st.session_state.pop('username', None)
        st.session_state.pop('selected_app', None)
        st.experimental_rerun()

def run_selected_app():
    if st.session_state['selected_app'] == "RQUARTZ - IMON":
        app1.main()
    elif st.session_state['selected_app'] == "RQUARTZ - T2F":
        app2.main()

if __name__ == '__main__':
    main()
