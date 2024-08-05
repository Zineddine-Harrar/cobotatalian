import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px  # Assurez-vous d'importer plotly.express pour px.bar
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
    planning_df = pd.read_csv('ECOBOT40.csv', delimiter=';', encoding='ISO-8859-1')
    details_df = pd.read_csv('DATASET/ECOBOT40/05-08.csv', encoding='ISO-8859-1', delimiter=';', on_bad_lines='skip')

    # Nettoyer les colonnes dans details_df0
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
    # Fonction pour nettoyer les doublons
    def clean_duplicates(details_df):
        # Convertir les colonnes "début" et "fin" en format datetime
        details_df['task_start_time'] = pd.to_datetime(details_df['task_start_time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    
        # Extraire la date de début
        details_df['date'] = details_df['task_start_time'].dt.date
    
        # Garder la ligne avec le plus haut pourcentage de complétion pour chaque groupe (location, route, date)
        details_df = details_df.loc[details_df.groupby(['cleaning_plan', 'date'])['task_completion_(%)'].idxmax()]
    
        # Additionner les colonnes surface, durée et distance pour chaque groupe
        sum_columns = ['actual_cleaning_area(?)', 'total_time_(h)', 'work_efficiency_(?/h)']
        details_df[sum_columns] = details_df.groupby(['cleaning_plan', 'task_start_time'])[sum_columns].transform('sum')
    
        return details_df

    # Nettoyer les doublons dans le dataframe details_df
    details_df1 = clean_duplicates(details_df)
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

    testcomp = create_parcours_comparison_table(28, details_df, planning_df)

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
        return completion_rates, weekly_completion_rate

    completion_rates, weekly_completion_rate = calculate_weekly_completion_rate(details_df, 28)
    print(weekly_completion_rate)

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
    st.title('Indicateurs de Suivi des Parcours du ECOBOT 40')

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

    weekly_comparison_table = create_parcours_comparison_table(semaine, details_df1, planning_df)
    taux_suivi = calculate_taux_suivi_from_table(weekly_comparison_table)
    completion_rates, weekly_completion_rate = calculate_weekly_completion_rate(details_df1, semaine)
    heures_cumulees, surface_nettoyee, productivite_moyenne = calculate_weekly_indicators(details_df, semaine)

    st.markdown("## **Indicateurs Hebdomadaires**")
    col1, col2, col3 = st.columns(3)

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

    completion_rates_df = completion_rates.reset_index()
    # Renommer les colonnes pour supprimer les caractères spéciaux
    completion_rates_df.columns = ['cleaning_plan', 'task_completion_(%)']

    # Créer l'histogramme des taux de complétion par parcours
    fig_hist = px.bar(completion_rates_df, x='cleaning_plan', y='task_completion_(%)',
                      title='Taux de Complétion Hebdomadaire par Parcours',
                      labels={'cleaning_plan': 'Parcours', 'task_completion_(%)': 'Taux de Complétion (%)'},
                      template='plotly_dark')

    # Afficher l'histogramme dans Streamlit
    st.plotly_chart(fig_hist)

if __name__ == '__main__':
    main()
