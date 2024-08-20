import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.io as pio
from plotly.subplots import make_subplots

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
    planning_df = pd.read_csv('PLANNING RQUARTZ T2F.csv', delimiter=';', encoding='ISO-8859-1')
    details_df = pd.read_csv('DATASET/T2F/19-08.csv', encoding='ISO-8859-1', delimiter=';', on_bad_lines='skip')

    # Nettoyer les colonnes dans details_df
    details_df.columns = details_df.columns.str.replace('\r\n', '').str.strip()
    details_df.columns = details_df.columns.str.replace(' ', '_').str.lower()

    details_df['début'] = pd.to_datetime(details_df['début'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    details_df['fin'] = pd.to_datetime(details_df['fin'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    
    # Extraire le jour de la semaine, la date et le mois de début
    details_df['jour'] = details_df['début'].dt.day_name()
    details_df['date'] = details_df['début'].dt.date
    details_df['mois'] = details_df['début'].dt.to_period('M')

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

    # Nettoyer les doublons
    def clean_duplicates(details_df):
        details_df['début'] = pd.to_datetime(details_df['début'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        details_df['fin'] = pd.to_datetime(details_df['fin'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        details_df['date'] = details_df['début'].dt.date
        details_df = details_df.loc[details_df.groupby(['parcours', 'date'])['terminerà_[%]'].idxmax()]
        sum_columns = ['surfacepropre_[mq]', 'durée[mn]']
        details_df[sum_columns] = details_df.groupby(['parcours', 'début'])[sum_columns].transform('sum')
        return details_df

    details_df1 = clean_duplicates(details_df)

    # Option de sélection pour le type d'affichage
    option = st.selectbox("Choisissez l'affichage des KPI", ["Par semaine", "Par mois"])

    if option == "Par semaine":
        # Affichage des KPI par semaine
        week_start_dates = get_week_start_dates(2024)
        week_options = {week: date for week, date in week_start_dates.items()}
        selected_week = st.selectbox("Sélectionnez le numéro de la semaine", options=list(week_options.keys()), format_func=lambda x: f"Semaine {x} ({week_options[x].strftime('%d/%m/%Y')})")
        semaine = selected_week

        weekly_comparison_table = create_parcours_comparison_table(semaine, details_df1, planning_df)
        taux_suivi = calculate_taux_suivi_from_table(weekly_comparison_table)
        weekly_completion_rate, completion_rates = calculate_weekly_completion_rate(details_df1, semaine)
        heures_cumulees, surface_nettoyee, vitesse_moyenne, productivite_moyenne = calculate_weekly_indicators(details_df, semaine)
        weekly_cost, hourly_cost, total_cost, utilization_rate = calculate_weekly_hourly_cost(heures_cumulees)

        # Afficher les KPI hebdomadaires
        display_kpi(heures_cumulees, surface_nettoyee, vitesse_moyenne, productivite_moyenne, total_cost, hourly_cost, utilization_rate)
        display_gauges(taux_suivi, weekly_completion_rate)
        display_comparison_table(weekly_comparison_table)
        display_completion_histogram(completion_rates)

    elif option == "Par mois":
        # Affichage des KPI par mois
        selected_month = st.selectbox("Sélectionnez un mois", options=details_df['mois'].unique())
        mois = selected_month

        heures_cumulees, surface_nettoyee, vitesse_moyenne, productivite_moyenne = calculate_monthly_indicators(details_df, mois)
        monthly_completion_rate, completion_rates = calculate_monthly_completion_rate(details_df1, mois)
        monthly_cost, hourly_cost, total_cost, utilization_rate = calculate_weekly_hourly_cost(heures_cumulees)

        # Afficher les KPI mensuels
        display_kpi(heures_cumulees, surface_nettoyee, vitesse_moyenne, productivite_moyenne, total_cost, hourly_cost, utilization_rate)
        display_gauges(None, monthly_completion_rate)
        display_completion_histogram(completion_rates)

# Fonctions utilitaires
def display_kpi(heures_cumulees, surface_nettoyee, vitesse_moyenne, productivite_moyenne, total_cost, hourly_cost, utilization_rate):
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"<div class='metric-container'><div class='metric-label'>Heures cumulées</div><div class='metric-value'>{heures_cumulees:.2f} heures</div></div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"<div class='metric-container'><div class='metric-label'>Surfaces nettoyées cumulées</div><div class='metric-value'>{surface_nettoyee:.2f} m²</div></div>", unsafe_allow_html=True)

    with col3:
        st.markdown(f"<div class='metric-container'><div class='metric-label'>Productivité moyenne</div><div class='metric-value'>{productivite_moyenne:.2f} m²/h</div></div>", unsafe_allow_html=True)

    with col4:
        st.markdown(f"<div class='metric-container'><div class='metric-label'>Vitesse moyenne</div><div class='metric-value'>{vitesse_moyenne:.2f} km/h</div></div>", unsafe_allow_html=True)

    with col5:
        st.markdown(f"<div class='metric-container'><div class='metric-label'>Coût total</div><div class='metric-value'>{total_cost:.2f} €</div><div class='metric-delta'>Coût/h: {hourly_cost:.2f} €</div></div>", unsafe_allow_html=True)

    with col6:
        st.markdown(f"<div class='metric-container'><div class='metric-label'>Taux d'utilisation</div><div class='metric-value'>{utilization_rate:.2f} %</div></div>", unsafe_allow_html=True)

def display_gauges(taux_suivi=None, completion_rate=None):
    col1, col2 = st.columns(2)
    
    if taux_suivi is not None:
        fig_suivi = create_gauge_chart(taux_suivi, "Taux de suivi des parcours")
        with col1:
            st.subheader('Taux de Suivi')
            st.plotly_chart(fig_suivi)

    if completion_rate is not None:
        fig_completion = create_gauge_chart(completion_rate, "Taux de réalisation des parcours")
        with col2:
            st.subheader('Taux de réalisation des parcours')
            st.plotly_chart(fig_completion)

def create_gauge_chart(value, title):
    return go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title},
        gauge={
            'axis': {'range': [None, 100]},
            'steps': [
                {'range': [0, 50], 'color': "orange"},
                {'range': [50, 100], 'color': "green"}],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': value}
        }
    )).update_layout(paper_bgcolor="black", plot_bgcolor="black", font={'color': "white"})

def display_comparison_table(comparison_table):
    styled_table = comparison_table.style.applymap(style_cell)
    styled_table = styled_table.applymap(lambda x: 'background-color: black; color: white;', subset=['Parcours Prévu'])
    styled_table = styled_table.set_table_styles([{'selector': 'thead th', 'props': [('background-color', 'black'), ('color', 'white')]}])
    st.subheader('Tableau de Suivi des Parcours')
    st.dataframe(styled_table, width=2000)

def display_completion_histogram(completion_rates_df):
    fig_hist = px.bar(completion_rates_df, x='parcours', y='taux_completion', title='Taux de réalisation par parcours', labels={'parcours': 'Parcours', 'taux_completion': 'Taux de réalisation (%)'}, template='plotly_dark')
    st.plotly_chart(fig_hist)

# Lancer l'application
if __name__ == '__main__':
    main()
