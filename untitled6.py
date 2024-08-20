import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.io as pio
from plotly.subplots import make_subplots

def get_week_start_dates(year):
    start_date = datetime(year, 1, 1)
    if start_date.weekday() > 0:  # Si le 1er janvier n'est pas un lundi
        start_date += timedelta(days=(7 - start_date.weekday()))  # Aller au prochain lundi
    week_dates = {}
    for week in range(1, 54):  # Assumer jusqu'à 53 semaines
        week_dates[week] = start_date + timedelta(weeks=(week - 1))
    return week_dates

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

def calculate_taux_suivi_from_table(comparison_table):
    # Calculer le nombre total de parcours
    total_parcours = comparison_table.shape[0] * (comparison_table.shape[1] - 1)  # Parcours par jours de la semaine
    parcours_faits = comparison_table.apply(lambda row: row[1:].tolist().count("Fait"), axis=1).sum()
    
    # Calculer le taux de suivi
    taux_suivi = (parcours_faits / total_parcours) * 100 if total_parcours > 0 else 0
    
    return taux_suivi
def calculate_weekly_completion_rate(details_df, planning_df, semaine):
    weekly_details = details_df[details_df['semaine'] == semaine]
    parcours_counts = weekly_details.groupby('parcours').size()
    parcours_planned = planning_df[planning_df['semaine'] == semaine]['parcours'].unique()
    completion_rates = []
    for parcours in parcours_planned:
        if parcours in parcours_counts:
            taux_completion = (parcours_counts[parcours] / planning_df[(planning_df['semaine'] == semaine) & (planning_df['parcours'] == parcours)].shape[0]) * 100
        else:
            taux_completion = 0
        completion_rates.append({'parcours': parcours, 'taux_completion': taux_completion})
    weekly_completion_rate = sum(row['taux_completion'] for row in completion_rates) / len(completion_rates) if completion_rates else 0
    return weekly_completion_rate, pd.DataFrame(completion_rates)


def calculate_monthly_completion_rate(details_df, planning_df, mois):
    monthly_details = details_df[details_df['mois'] == mois]
    planning_df_monthly = planning_df[planning_df['semaine'].isin(details_df[details_df['mois'] == mois]['semaine'].unique())]
    planning_df_monthly, monthly_details = planning_df_monthly.align(monthly_details, axis=0, copy=False)
    parcours_counts = monthly_details.groupby('parcours').size()
    parcours_planned = planning_df_monthly['parcours'].unique()
    completion_rates = []
    for parcours in parcours_planned:
        if parcours in parcours_counts:
            taux_completion = (parcours_counts[parcours] / planning_df_monthly[planning_df_monthly['parcours'] == parcours].shape[0]) * 100
        else:
            taux_completion = 0
        completion_rates.append({'parcours': parcours, 'taux_completion': taux_completion})
    monthly_completion_rate = sum(row['taux_completion'] for row in completion_rates) / len(completion_rates) if completion_rates else 0
    return monthly_completion_rate, pd.DataFrame(completion_rates)
    
def calculate_weekly_indicators(details_df, semaine):
    weekly_details = details_df[details_df['semaine'] == semaine]
    heures_cumulees = weekly_details['durée[mn]'].sum() / 60
    surface_nettoyee = weekly_details['surfacepropre_[mq]'].sum()
    vitesse_moyenne = weekly_details['vitesse_moyenne[km/h]'].mean()
    productivite_moyenne = weekly_details['productivitéhoraire_[mq/h]'].mean()
    return heures_cumulees, surface_nettoyee, vitesse_moyenne, productivite_moyenne

def calculate_monthly_indicators(details_df, mois):
    monthly_details = details_df[details_df['mois'] == mois]
    heures_cumulees = monthly_details['durée[mn]'].sum() / 60
    surface_nettoyee = monthly_details['surfacepropre_[mq]'].sum()
    vitesse_moyenne = monthly_details['vitesse_moyenne[km/h]'].mean()
    productivite_moyenne = monthly_details['productivitéhoraire_[mq/h]'].mean()
    return heures_cumulees, surface_nettoyee, vitesse_moyenne, productivite_moyenne

def calculate_weekly_hourly_cost(heures_cumulees):
    total_cost = 1000  # Coût total hypothétique
    hourly_cost = total_cost / heures_cumulees if heures_cumulees > 0 else 0
    utilization_rate = (heures_cumulees / 40) * 100  # Hypothèse de 40 heures par semaine
    return hourly_cost, total_cost, utilization_rate



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
        weekly_completion_rate, completion_rates = calculate_weekly_completion_rate(details_df1, planning_df, semaine)
        heures_cumulees, surface_nettoyee, vitesse_moyenne, productivite_moyenne = calculate_weekly_indicators(details_df, semaine)
        hourly_cost, total_cost, utilization_rate = calculate_weekly_hourly_cost(heures_cumulees)

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
        monthly_completion_rate, completion_rates = calculate_monthly_completion_rate(details_df1, planning_df, mois)
        hourly_cost, total_cost, utilization_rate = calculate_weekly_hourly_cost(heures_cumulees)

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
