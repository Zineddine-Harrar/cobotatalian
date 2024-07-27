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

# Fonction pour rediriger avec JavaScript
def js_redirect(url):
    js_code = f"""
        <script>
            window.location.href = "{url}";
        </script>
    """
    st.write(js_code, unsafe_allow_html=True)

# Fonction principale
def main():
    st.set_page_config(page_title="ATALIAN COBOT", layout="wide")
    # Ajouter des styles CSS personnalisés pour le fond noir et le texte blanc
    st.markdown(
        """
        <style>
        .stApp {
            background-color: black;
            color: white;
        }
        .stTextInput>div>div>input {
            background-color: black;
            color: white;
        }
        .stTextInput>label {
            color: white;
        }
        .stButton>button {
            background-color: black;
            color: white;
            border: 2px solid white;
            padding: 10px;
            margin: 10px;
        }
        .stMetric>div>div>div>span {
            color: white;
        }
        .stTitle, .stHeader, .stSubheader, .stMarkdown {
            color: white;
        }
        .custom-title {
            color: #ff6347;
        }
        .stAlert>div {
            background-color: #444;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if 'username' not in st.session_state:
        st.session_state['username'] = ''

    if 'selected_app' not in st.session_state:
        st.session_state['selected_app'] = None

    query_params = st.query_params
    if 'logged_in' in query_params and query_params['logged_in'] == 'true':
        st.session_state['logged_in'] = True

    if 'logged_in' in query_params and query_params['logged_in'] == 'false':
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        app_selection_page()
    else:
        login_section()

# Section de connexion
def login_section():
    st.markdown('<h1 class="custom-title">Connexion Interface de visualisation ATALIAN / COBOT</h1>', unsafe_allow_html=True)
    st.image("atalian-logo (1).png", width=300)  # Chemin vers votre logo

    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type='password')
    if st.button("Connexion"):
        if login(username, password):
            st.success(f"Bienvenue {username}")
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.query_params.update({"logged_in": "true"})
            js_redirect(f"{st.get_url()}?logged_in=true")
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect")

# Page de sélection de l'application
def app_selection_page():
    # Afficher les logos côte à côte
    logo_path1 = "atalian-logo (1).png"
    st.image(logo_path1, width=150)  # Ajustez la largeur selon vos besoins
    st.markdown('<h1 class="custom-title">Applications RQUARTZ</h1>', unsafe_allow_html=True)
    if st.button("Déconnexion"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.session_state['selected_app'] = None
        st.query_params.update({"logged_in": "false"})
        js_redirect(f"{st.get_url()}?logged_in=false")

    st.markdown("### Sélectionnez une application")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("RQUARTZ - IMON"):
            st.session_state['selected_app'] = "RQUARTZ - IMON"
            st.query_params.update({"app": "rquartz_imon"})
            js_redirect(f"{st.get_url()}?app=rquartz_imon")

    with col2:
        if st.button("RQUARTZ - T2F"):
            st.session_state['selected_app'] = "RQUARTZ - T2F"
            st.query_params.update({"app": "rquartz_t2f"})
            js_redirect(f"{st.get_url()}?app=rquartz_t2f")
            
    with col3:
        if st.button("ECOBOT 40"):
            st.session_state['selected_app'] = "ECOBOT 40"
            st.query_params.update({"app": "ecobot_40"})
            js_redirect(f"{st.get_url()}?app=ecobot_40")

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

# Fonction pour rediriger avec JavaScript
def js_redirect(url):
    js_code = f"""
        <script>
            window.location.href = "{url}";
        </script>
    """
    st.write(js_code, unsafe_allow_html=True)

# Fonction principale
def main():
    st.set_page_config(page_title="ATALIAN COBOT", layout="wide")
    # Ajouter des styles CSS personnalisés pour le fond noir et le texte blanc
    st.markdown(
        """
        <style>
        .stApp {
            background-color: black;
            color: white;
        }
        .stTextInput>div>div>input {
            background-color: black;
            color: white;
        }
        .stTextInput>label {
            color: white;
        }
        .stButton>button {
            background-color: black;
            color: white;
            border: 2px solid white;
            padding: 10px;
            margin: 10px;
        }
        .stMetric>div>div>div>span {
            color: white;
        }
        .stTitle, .stHeader, .stSubheader, .stMarkdown {
            color: white;
        }
        .custom-title {
            color: #ff6347;
        }
        .stAlert>div {
            background-color: #444;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if 'username' not in st.session_state:
        st.session_state['username'] = ''

    if 'selected_app' not in st.session_state:
        st.session_state['selected_app'] = None

    query_params = st.query_params
    if 'logged_in' in query_params and query_params['logged_in'] == 'true':
        st.session_state['logged_in'] = True

    if 'logged_in' in query_params and query_params['logged_in'] == 'false':
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        app_selection_page()
    else:
        login_section()

# Section de connexion
def login_section():
    st.markdown('<h1 class="custom-title">Connexion Interface de visualisation ATALIAN / COBOT</h1>', unsafe_allow_html=True)
    st.image("atalian-logo (1).png", width=300)  # Chemin vers votre logo

    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type='password')
    if st.button("Connexion"):
        if login(username, password):
            st.success(f"Bienvenue {username}")
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.query_params.update({"logged_in": "true"})
            js_redirect(f"{st.get_url()}?logged_in=true")
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect")

# Page de sélection de l'application
def app_selection_page():
    # Afficher les logos côte à côte
    logo_path1 = "atalian-logo (1).png"
    st.image(logo_path1, width=150)  # Ajustez la largeur selon vos besoins
    st.markdown('<h1 class="custom-title">Applications RQUARTZ</h1>', unsafe_allow_html=True)
    if st.button("Déconnexion"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.session_state['selected_app'] = None
        st.query_params.update({"logged_in": "false"})
        js_redirect(f"{st.get_url()}?logged_in=false")

    st.markdown("### Sélectionnez une application")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("RQUARTZ - IMON"):
            st.session_state['selected_app'] = "RQUARTZ - IMON"
            st.query_params.update({"app": "rquartz_imon"})
            js_redirect(f"{st.get_url()}?app=rquartz_imon")

    with col2:
        if st.button("RQUARTZ - T2F"):
            st.session_state['selected_app'] = "RQUARTZ - T2F"
            st.query_params.update({"app": "rquartz_t2f"})
            js_redirect(f"{st.get_url()}?app=rquartz_t2f")
            
    with col3:
        if st.button("ECOBOT 40"):
            st.session_state['selected_app'] = "ECOBOT 40"
            st.query_params.update({"app": "ecobot_40"})
            js_redirect(f"{st.get_url()}?app=ecobot_40")

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
