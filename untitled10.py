import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import matplotlib.pyplot as plt

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
         </style>
         """,
         unsafe_allow_html=True
    )
     
    # Charger les fichiers CSV
    planning_df = pd.read_csv('ECOBOT40.csv', delimiter=';', encoding='ISO-8859-1')
    details_df = pd.read_csv('TaskReport_Atalian_ADP_20240717120151.csv', encoding='ISO-8859-1', delimiter=';', on_bad_lines='skip')

    # Nettoyer les colonnes dans details_df
    details_df.columns = details_df.columns.str.replace('\r\n', '').str.strip()
    details_df.columns = details_df.columns.str.replace(' ', '_').str.lower()

    # Convertir la colonne task_start_time en type datetime
    details_df['task_start_time'] = pd.to_datetime(details_df['task_start_time'])

    # Utiliser l'accessor .dt pour obtenir le nom du jour
    details_df['jour'] = details_df['task_start_time'].dt.day_name()
    # Ajouter la colonne semaine
    details_df['semaine'] = details_df['task_start_time'].dt.isocalendar().week

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
    numeric_columns = ['total_time_(h)', 'actual_cleaning_area(?)','cleaning_plan_area_(?)']
    for col in numeric_columns:
        details_df[col] = pd.to_numeric(details_df[col].astype(str).str.replace(',', ''), errors='coerce')

    # Ajouter les colonnes "jour" et "semaine" à planning_df
    planning_df = planning_df.melt(var_name='jour_fr', value_name='parcours').dropna()

    # Ajouter la colonne semaine à planning_df
    def add_weeks_to_planning_df(planning_df):
        start_date = datetime(2024, 1, 1)
        planning_df['date'] = pd.to_datetime(planning_df.index, unit='D', origin=start_date)
        planning_df['semaine'] = planning_df['date'].dt.isocalendar().week
        return planning_df

    planning_df = add_weeks_to_planning_df(planning_df)

    def create_parcours_comparison_table(semaine, details_df, planning_df):
        weekly_details = details_df[details_df['semaine'] == semaine]
        days_of_week_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        parcours_list = set(planning_df['parcours'])
        parcours_list.discard(None)
        comparison_table = pd.DataFrame(columns=['Parcours Prévu'] + days_of_week_fr)
        parcours_status = {parcours: {day: "Pas fait" for day in days_of_week_fr} for parcours in parcours_list}

        for day in days_of_week_fr:
            planned_routes = planning_df[(planning_df['jour_fr'] == day) & (planning_df['semaine'] == semaine)]['parcours'].str.strip().str.lower().tolist()
            actual_routes = weekly_details[weekly_details['jour_fr'] == day]['cleaning_plan'].astype(str).str.strip().str.lower().tolist()
            for parcours in parcours_list:
                parcours_normalized = parcours.strip().lower()
                if parcours_normalized in actual_routes:
                    parcours_status[parcours][day] = "Fait"

        rows = []
        for parcours, status in parcours_status.items():
            row = {'Parcours Prévu': parcours}
            row.update(status)
            rows.append(row)

        comparison_table = pd.DataFrame(rows)
        return comparison_table
    testcomp = create_parcours_comparison_table(28
                                            , details_df, planning_df)
    # Fonction pour calculer le taux de suivi à partir du tableau de suivi
    def calculate_taux_suivi_from_table(comparison_table):
        total_parcours = 28
        parcours_faits = comparison_table.apply(lambda row: list(row[1:]).count("Fait"), axis=1).sum()
        taux_suivi = (parcours_faits / total_parcours) * 100 if total_parcours > 0 else 0
        return taux_suivi
    
    testtaux = calculate_taux_suivi_from_table(testcomp)
    print(testtaux)
    # Fonction pour calculer le taux de complétion hebdomadaire
    def calculate_weekly_completion_rate(details_df, semaine):
        weekly_details = details_df[details_df['semaine'] == semaine]
        completion_rates = weekly_details.groupby('cleaning_plan')['task_completion_(%)'].mean()
        completed_routes = (completion_rates >= 90).sum()
        total_routes = len(completion_rates)
        weekly_completion_rate = (completed_routes / total_routes) * 100 if total_routes > 0 else 0
        return weekly_completion_rate
    testcompletion = calculate_weekly_completion_rate(details_df, 28)
    print(testcompletion)
    # Fonction pour calculer les indicateurs hebdomadaires
    def calculate_weekly_indicators(details_df, semaine):
        weekly_details = details_df[details_df['semaine'] == semaine]
        heures_cumulees = weekly_details['total_time_(h)'].sum()
        surface_nettoyee = weekly_details['actual_cleaning_area(?)'].sum()
        productivite_moyenne = weekly_details['work_efficiency_(?/h)'].mean()
        return heures_cumulees, surface_nettoyee, productivite_moyenne
    
    testkpi = calculate_weekly_indicators(details_df, 28)
    print(testkpi)

# Interface Streamlit
    logo_path1 = "atalian-logo (1).png"
    st.image(logo_path1, width=150)

    st.title('Indicateurs de Suivi des Parcours du ECOBOT 40')

    semaine = st.number_input("Sélectionnez le numéro de la semaine", min_value=1, max_value=53, value=28)

    weekly_comparison_table = create_parcours_comparison_table(semaine, details_df, planning_df)
    taux_suivi = calculate_taux_suivi_from_table(weekly_comparison_table)
    weekly_completion_rate = calculate_weekly_completion_rate(details_df, semaine)
    heures_cumulees, surface_nettoyee, productivite_moyenne = calculate_weekly_indicators(details_df, semaine)

    st.subheader('Indicateurs Hebdomadaires')
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Heures cumulées", value=f"{heures_cumulees:.2f} heures")

    with col2:
        st.metric(label="Surface nettoyée", value=f"{surface_nettoyee:.2f} m²")

    with col3:
        st.metric(label="Productivité moyenne", value=f"{productivite_moyenne:.2f} m²/h")

    fig_suivi = go.Figure(go.Indicator(
        mode="gauge+number",
        value=taux_suivi,
        title={'text': "Taux de Suivi"},
        gauge={
            'axis': {'range': [None, 100]},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 100], 'color': "green"}],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': taux_suivi}}))

    fig_completion = go.Figure(go.Indicator(
        mode="gauge+number",
        value=weekly_completion_rate,
        title={'text': "Taux de Complétion Hebdomadaire"},
        gauge={
            'axis': {'range': [None, 100]},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 100], 'color': "green"}],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': weekly_completion_rate}}))

    col1, col2 = st.columns(2)

    with col1:
        st.subheader('Taux de Suivi')
        st.plotly_chart(fig_suivi)

    with col2:
        st.subheader('Taux de Complétion')
        st.plotly_chart(fig_completion)

    st.subheader('Tableau de Suivi des Parcours')
    st.dataframe(weekly_comparison_table, width=2000)


if __name__ == '__main__':
    main()

