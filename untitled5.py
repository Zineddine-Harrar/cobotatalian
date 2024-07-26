import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

def main():

    st.markdown(
        """
        <style>
        .stApp {
            background-color: orange;
            color: black;
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
            color: black;
        }
        .custom-title {
            color: #ff6347;
        }
        .stAlert>div {
            background-color: #444;
            color: white;
        }
        .metric-container {
            border-radius: 10px;
            background-color: #1e1e1e;
            padding: 20px;
            text-align: center;
            color: #fff;
        }
        .metric-label {
            font-size: 1.5em;
            font-weight: bold;
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
        }
        .metric-delta {
            font-size: 1.2em;
            color: #28a745;
        }
        .dataframe {
            background-color: #000 !important;
        }
        .dataframe thead th {
            background-color: #000 !important;
            color: #fff !important;
        }
        .dataframe tbody td {
            background-color: #000 !important;
            color: #fff !important;
        }
        .dataframe tbody td[data-val='Fait'] {
            background-color: #13FF1A !important;
            color: black !important;
        }
        .dataframe tbody td[data-val='Pas fait'] {
            background-color: #FF1313 !important;
            color: #CACFD2 !important;
        }
        .dataframe tbody td:first-child {
            background-color: #000 !important;
            color: #fff !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


    # Charger les fichiers CSV
    planning_df = pd.read_csv('PLANNING RQUARTZ IMON  (1).csv', delimiter=';', encoding='ISO-8859-1')
    details_df = pd.read_csv('DATASET/IMON/19-07 (3) (1).csv', encoding='ISO-8859-1', delimiter=';', on_bad_lines='skip')
    
    # Nettoyer les colonnes dans details_df
    details_df.columns = details_df.columns.str.replace('\r\n', '').str.strip()
    details_df.columns = details_df.columns.str.replace(' ', '_').str.lower()

    # Convertir les colonnes "début" et "fin" en format datetime
    details_df['début'] = pd.to_datetime(details_df['début'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    details_df['fin'] = pd.to_datetime(details_df['fin'], format='%d/%m/%Y %H:%M', errors='coerce')
    print(details_df['début'])
    # Extraire le jour de la semaine et la date de début
    details_df['jour'] = details_df['début'].dt.day_name()
    details_df['date'] = details_df['début'].dt.date

    # Ajouter la colonne semaine
    details_df['semaine'] = details_df['début'].dt.isocalendar().week

    # Dictionnaire pour traduire les noms des jours de l'anglais au français
    day_translation = {
        'Monday': 'Lundi',
        'Tuesday': 'Mardi',
        'Wednesday': 'Mercredi',
        'Thursday': 'Jeudi',
        'Friday': 'Vendredi',
        'Saturday': 'Samedi',
        'Sunday': 'Dimanche'
    }
    details_df['jour_fr'] = details_df['jour'].map(day_translation)

    # Convertir les colonnes pertinentes en format numérique
    numeric_columns = ['durée[mn]', 'surfacepropre_[mq]', 'vitesse_moyenne[km/h]', 'productivitéhoraire_[mq/h]']
    for col in numeric_columns:
        details_df[col] = pd.to_numeric(details_df[col].astype(str).str.replace(',', '.'), errors='coerce')

    # Ajouter les colonnes "jour" et "semaine" à planning_df
    planning_df = planning_df.melt(var_name='jour_fr', value_name='parcours').dropna()

    # Ajouter la colonne semaine à planning_df
    def add_weeks_to_planning_df(planning_df):
        start_date = datetime(2024, 1, 1)
        planning_df['date'] = pd.to_datetime(planning_df.index, unit='D', origin=start_date)
        planning_df['semaine'] = planning_df['date'].dt.isocalendar().week
        return planning_df

    planning_df = add_weeks_to_planning_df(planning_df)

    # Fonction pour créer le tableau de suivi par parcours pour une semaine spécifique
    def create_parcours_comparison_table(semaine, details_df, planning_df):
        # Filtrer les données pour la semaine spécifiée
        weekly_details = details_df[details_df['semaine'] == semaine]
        
        # Initialiser le tableau de suivi
        days_of_week_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        parcours_list = set(planning_df['parcours'])
        parcours_list.discard(None)
        comparison_table = pd.DataFrame(columns=['Parcours Prévu'] + days_of_week_fr)
        
        # Initialiser un dictionnaire pour stocker les statuts des parcours
        parcours_status = {parcours: {day: "Pas fait" for day in days_of_week_fr} for parcours in parcours_list}
        
        for day in days_of_week_fr:
            # Parcours prévus pour le jour
            planned_routes = planning_df[(planning_df['jour_fr'] == day) & (planning_df['semaine'] == semaine)]['parcours'].str.strip().str.lower().tolist()
            
            # Parcours réalisés pour le jour
            actual_routes = weekly_details[weekly_details['jour_fr'] == day]['parcours'].str.strip().str.lower().tolist()
            
            # Comparer les parcours prévus et réalisés
            for parcours in parcours_list:
                parcours_normalized = parcours.strip().lower()
                if parcours_normalized in actual_routes:
                    parcours_status[parcours][day] = "Fait"
        
        # Créer le DataFrame à partir du dictionnaire de statuts
        rows = []
        for parcours, status in parcours_status.items():
            row = {'Parcours Prévu': parcours}
            row.update(status)
            rows.append(row)
        
        comparison_table = pd.DataFrame(rows)
        
        return comparison_table

    # Fonction pour calculer le taux de suivi à partir du tableau de suivi
    def calculate_taux_suivi_from_table(comparison_table):
        total_parcours = 49  # Total des parcours prévus sur une semaine (7 jours * 6 parcours par jour)
        parcours_faits = comparison_table.apply(lambda row: list(row[1:]).count("Fait"), axis=1).sum()
        
        taux_suivi = (parcours_faits / total_parcours) * 100 if total_parcours > 0 else 0
        
        return taux_suivi

    # Fonction pour calculer le taux de complétion hebdomadaire
    def calculate_weekly_completion_rate(details_df, semaine):
        # Filtrer les données pour la semaine spécifiée
        weekly_details = details_df[details_df['semaine'] == semaine]
        # Calculer le taux de complétion pour chaque parcours
        completion_rates = weekly_details.groupby('parcours')['terminerà_[%]'].mean()
        # Calculer le taux de complétion hebdomadaire
        completed_routes = (completion_rates >= 90).sum()
        total_routes = len(completion_rates)
        weekly_completion_rate = (completed_routes / total_routes) * 100 if total_routes > 0 else 0
        return weekly_completion_rate, completion_rates

    # Fonction pour calculer les indicateurs hebdomadaires
    def calculate_weekly_indicators(details_df, semaine):
        # Filtrer les données pour la semaine spécifiée
        weekly_details = details_df[details_df['semaine'] == semaine]
        
        # Calculer les indicateurs
        heures_cumulees = weekly_details['durée[mn]'].sum() / 60  # Convertir les minutes en heures
        surface_nettoyee = weekly_details['surfacepropre_[mq]'].sum()
        vitesse_moyenne = weekly_details['vitesse_moyenne[km/h]'].mean()
        productivite_moyenne = weekly_details['productivitéhoraire_[mq/h]'].mean()
        
        return heures_cumulees, surface_nettoyee, vitesse_moyenne, productivite_moyenne

    # Interface Streamlit

    st.title('Indicateurs de Suivi des Parcours du RQUARTZ IMON')

    # Créer un dictionnaire pour mapper chaque semaine à la date de début de la semaine
    def get_week_start_dates(year):
        start_date = datetime(year, 1, 1)
        if start_date.weekday() > 0:  # Si le 1er janvier n'est pas un lundi
            start_date += timedelta(days=(7 - start_date.weekday()))  # Aller au prochain lundi
        week_dates = {}
        for week in range(28, 54):  # Assumer jusqu'à 53 semaines
            week_dates[week] = start_date + timedelta(weeks=(week - 1))
        return week_dates

    week_start_dates = get_week_start_dates(2024)
    week_options = {week: date for week, date in week_start_dates.items()}

   # Afficher le sélecteur de semaine avec les dates
    selected_week = st.selectbox("Sélectionnez le numéro de la semaine", options=list(week_options.keys()), format_func=lambda x: f"Semaine {x} ({week_options[x].strftime('%d/%m/%Y')})")

    # Sélection de la semaine
    semaine = selected_week
    # Créer le tableau de suivi par parcours pour la semaine spécifiée
    weekly_comparison_table = create_parcours_comparison_table(semaine, details_df, planning_df)
    

    # Calculer le taux de suivi à partir du tableau de suivi
    taux_suivi = calculate_taux_suivi_from_table(weekly_comparison_table)

    # Calculer le taux de complétion hebdomadaire
    weekly_completion_rate, completion_rates = calculate_weekly_completion_rate(details_df, semaine)

    

    # Calculer les indicateurs hebdomadaires
    heures_cumulees, surface_nettoyee, vitesse_moyenne, productivite_moyenne = calculate_weekly_indicators(details_df, semaine)

    # Afficher les KPI côte à côte
    st.markdown("## **Indicateurs Hebdomadaires**")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Heures cumulées</div>
                <div class="metric-value">{heures_cumulees:.2f} heures</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Surface nettoyée</div>
                <div class="metric-value">{surface_nettoyee:.2f} m²</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Productivité moyenne</div>
                <div class="metric-value">{productivite_moyenne:.2f} m²/h</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Vitesse moyenne</div>
                <div class="metric-value">{vitesse_moyenne:.2f} km/h</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    # Créer la jauge du taux de suivi
    fig_suivi = go.Figure(go.Indicator(
        mode="gauge+number",
        value=taux_suivi,
        title={'text': "Taux de Suivi"},
        gauge={
            'axis': {'range': [None, 100]},
            'steps': [
                {'range': [0, 50], 'color': "orange"},
                {'range': [50, 100], 'color': "green"}],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': taux_suivi}
        }
    ))

    # Mettre à jour le fond en noir
    fig_suivi.update_layout(
        paper_bgcolor="black",
        plot_bgcolor="black",
        font={'color': "white"}
    )

    # Créer la jauge du taux de complétion
    fig_completion = go.Figure(go.Indicator(
        mode="gauge+number",
        value=weekly_completion_rate,
        title={'text': "Taux de Complétion Hebdomadaire"},
        gauge={
            'axis': {'range': [None, 100]},
            'steps': [
                {'range': [0, 50], 'color': "orange"},
                {'range': [50, 100], 'color': "green"}],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': weekly_completion_rate}
        }
    ))

    # Mettre à jour le fond en noir
    fig_completion.update_layout(
        paper_bgcolor="black",
        plot_bgcolor="black",
        font={'color': "white"}
    )

    # Afficher les jauges côte à côte
    col1, col2 = st.columns(2)

    with col1:
        st.subheader('Taux de Suivi')
        st.plotly_chart(fig_suivi)

    with col2:
        st.subheader('Taux de Complétion')
        st.plotly_chart(fig_completion)

    # Appliquer le style conditionnel
    def style_cell(val):
        if val == 'Fait':
            return 'background-color: #13FF1A; color: black;'
        elif val == 'Pas fait':
            return 'background-color: #FF1313; color: #CACFD2;'
        else:
            return ''

    def style_header(val):
        return 'background-color: black; color: white;'

    # Appliquer le style sur tout le DataFrame
    styled_table = weekly_comparison_table.style.applymap(style_cell)
    
    # Appliquer le style sur la colonne "Parcours Prévu"
    styled_table = styled_table.applymap(lambda x: 'background-color: black; color: white;', subset=['Parcours Prévu'])
    # Appliquer le style sur les en-têtes de colonne
    styled_table = styled_table.set_table_styles([{'selector': 'thead th', 'props': [('background-color', 'black'), ('color', 'white')]}])

    # Afficher le tableau de suivi par parcours
    st.subheader('Tableau de Suivi des Parcours')
    st.dataframe(styled_table, width=2000)

    
if __name__ == '__main__':
    main()
