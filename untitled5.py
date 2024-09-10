import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.io as pio
from plotly.subplots import make_subplots
import openpyxl
import io
from supabase import create_client, Client
from streamlit.runtime.scriptrunner import RerunException
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
            border-radius: 10px;  /* Augmenté pour un look plus doux avec la taille accrue */
            background-color: #1e1e1e;
            padding: 30px;  /* Augmenté significativement pour plus d'espace */
            margin: 15px 0;  /* Augmenté pour plus d'espace entre les boîtes */
            text-align: center;
            color: #fff;
            min-height: 220px;  /* Augmenté significativement */
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .metric-label {
            font-size: 1.4em;  /* Augmenté pour s'adapter à la plus grande boîte */
            font-weight: bold;
            margin-bottom: 15px;  /* Augmenté pour plus d'espace */
        }

        .metric-value {
            font-size: 2.6em;  /* Augmenté pour une meilleure visibilité dans la grande boîte */
            font-weight: bold;
            line-height: 1.4;  /* Ajusté pour un meilleur espacement */
        }

        .metric-delta {
            font-size: 1.3em;  /* Augmenté proportionnellement */
            color: #28a745;
            margin-top: 12px;  /* Ajusté pour l'équilibre dans la grande boîte */
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
        .stDownloadButton button {
        color: black !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


    # Charger les fichiers CSV
    planning_df = pd.read_csv('PLANNING RQUARTZ IMON  (1).csv', delimiter=';', encoding='ISO-8859-1')
    details_df = pd.read_csv('DATASET/IMON/30-08.csv', encoding='ISO-8859-1', delimiter=';', on_bad_lines='skip')
    
    # Nettoyer les colonnes dans details_df
    details_df.columns = details_df.columns.str.replace('\r\n', '').str.strip()
    details_df.columns = details_df.columns.str.replace(' ', '_').str.lower()

    # Convertir les colonnes "début" et "fin" en format datetime
    details_df['début'] = pd.to_datetime(details_df['début'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    details_df['fin'] = pd.to_datetime(details_df['fin'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
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

    # Fonction pour nettoyer les doublons
    def clean_duplicates(details_df):
        # Convertir les colonnes "début" et "fin" en format datetime
        details_df['début'] = pd.to_datetime(details_df['début'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        details_df['fin'] = pd.to_datetime(details_df['fin'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    
        # Extraire la date de début
        details_df['date'] = details_df['début'].dt.date
    
        # Garder la ligne avec le plus haut pourcentage de complétion pour chaque groupe (location, route, date)
        details_df = details_df.loc[details_df.groupby(['parcours', 'date'])['terminerà_[%]'].idxmax()]
    
        # Additionner les colonnes surface, durée et distance pour chaque groupe
        sum_columns = ['surfacepropre_[mq]', 'durée[mn]']
        details_df[sum_columns] = details_df.groupby(['parcours', 'début'])[sum_columns].transform('sum')
    
        return details_df

    # Nettoyer les doublons dans le dataframe details_df
    details_df1 = clean_duplicates(details_df)

    # Fonction pour créer le tableau de suivi par parcours pour une semaine spécifique
    def create_parcours_comparison_table(semaine, details_df1, planning_df):
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
    def calculate_completion_rates(details_df, threshold=90):
        # Calculer le taux de complétion pour chaque parcours
        completion_rates = details_df.groupby('parcours')['terminerà_[%]'].mean()
    
        # Calculer le nombre de parcours réalisés (>= 90%)
        parcours_realises = (completion_rates >= threshold).sum()
        
        # Calculer le taux de réalisation
        total_parcours = len(completion_rates)
        taux_realisation = (parcours_realises / total_parcours) * 100 if total_parcours > 0 else 0
    
        return completion_rates, taux_realisation

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
    # Fonction pour calculer les indicateurs hebdomadaires
    def calculate_monthly_indicators(details_df, mois):
        # Filtrer les données pour la semaine spécifiée
        monthly_details = details_df[details_df['mois'] == mois]
        
        # Calculer les indicateurs
        heures_cumulees_mois = monthly_details['durée[mn]'].sum() / 60  # Convertir les minutes en heures
        surface_nettoyee_mois = monthly_details['surfacepropre_[mq]'].sum()

        # Moyennes mensuelles pour la productivité et la vitesse
        vitesse_moyenne_mois = monthly_details['vitesse_moyenne[km/h]'].mean()
        productivite_moyenne_mois = monthly_details['productivitéhoraire_[mq/h]'].mean()
        
        return heures_cumulees_mois, surface_nettoyee_mois, vitesse_moyenne_mois, productivite_moyenne_mois
    def calculate_average_resolution_time(df):
        df['Resolution Time'] = (df['Retour'] - df['Apparition']).dt.total_seconds() / 60
        avg_resolution_time = df.groupby('Description')['Resolution Time'].mean().reset_index()
        avg_resolution_time.columns = ['Description', 'Avg Resolution Time (min)']
        return avg_resolution_time
    def create_pie_chart(alert_summary, text_color='white'):
        fig_pie = px.pie(alert_summary, values='Alert Count', names='Description', 
                         title='Répartition des évènements',
                         template='plotly_dark',
                         hole=0.3)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label', textfont_color=text_color)
        return fig_pie

    # Variables pour le calcul du taux d'utilisation
    working_hours_per_day = 3  # Nombre d'heures de travail prévues par jour
    working_days_per_week = 5  # Nombre de jours de travail prévus par semaine

    def calculate_weekly_hourly_cost(heures_cumulees, monthly_cost=1600, weeks_per_month=4):
        # Coût hebdomadaire
        weekly_cost = monthly_cost / weeks_per_month
    
        # Calculer le coût horaire basé sur les heures cumulées de la semaine
        hourly_cost = weekly_cost / heures_cumulees if heures_cumulees > 0 else 0
    
        # Calculer le coût total pour la semaine
        total_cost = hourly_cost * heures_cumulees

        # Calcul du taux d'utilisation
        planned_weekly_hours = working_hours_per_day * working_days_per_week
        utilization_rate = (heures_cumulees / planned_weekly_hours) * 100 if planned_weekly_hours > 0 else 0

        return weekly_cost, hourly_cost, total_cost, utilization_rate
    description_evenements = pd.read_excel("Description des evenements.xlsx")
    # Load the dataset with appropriate header row
    file_path = "DATASET/ALERTE/IMON/Alerte IMON  19-08.xlsx"
    alarm_details_df = pd.read_excel(file_path, header=4)
    description_evenements = pd.read_excel("Description des evenements.xlsx")
    # Rename columns for easier access
    alarm_details_df.columns = ['Index', 'Code', 'Composant', 'Description', 'Apparition_Date', 'Apparition_Time', 'Retour_Date', 'Retour_Time', 'Modèle_machine', 'Machine_Description', 'N_de_série']

    # Convert 'Apparition_Date' and 'Retour_Date' columns to string format if not already
    alarm_details_df['Apparition_Date'] = alarm_details_df['Apparition_Date'].astype(str)
    alarm_details_df['Retour_Date'] = alarm_details_df['Retour_Date'].astype(str)

    # Combine 'Apparition_Date' and 'Apparition_Time' into a single datetime column
    alarm_details_df['Apparition'] = pd.to_datetime(alarm_details_df['Apparition_Date'] + ' ' + alarm_details_df['Apparition_Time'], format='%Y-%m-%d %H:%M:%S')

    # Combine 'Retour_Date' and 'Retour_Time' into a single datetime column
    alarm_details_df['Retour'] = pd.to_datetime(alarm_details_df['Retour_Date'] + ' ' + alarm_details_df['Retour_Time'], format='%Y-%m-%d %H:%M:%S')

    # Calculate resolution time in minutes
    alarm_details_df['Resolution Time'] = (alarm_details_df['Retour'] - alarm_details_df['Apparition']).dt.total_seconds() / 60
    alarm_details_df['mois'] = alarm_details_df['Apparition'].dt.month


    # Drop intermediate columns
    alarm_details_df.drop(columns=['Apparition_Date', 'Apparition_Time', 'Retour_Date', 'Retour_Time', 'Index'], inplace=True)

    # Function to filter data by week
    def filter_data_by_week(data, week_number):
        data['week'] = data['Apparition'].dt.isocalendar().week
        return data[data['week'] == week_number]
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

            
    if 'period_selection' not in st.session_state:
        st.session_state['period_selection'] = "Semaine"

    period_selection = st.selectbox(
        "Sélectionnez la période à analyser",
        ["Semaine", "Mois"],
        index=["Semaine", "Mois"].index(st.session_state['period_selection'])
    )

    st.session_state['period_selection'] = period_selection
    
    if period_selection == "Semaine":
        selected_week = st.selectbox("Sélectionnez le numéro de la semaine", options=list(week_options.keys()), format_func=lambda x: f"Semaine {x} ({week_options[x].strftime('%d/%m/%Y')})")

        # Sélection de la semaine
        semaine = selected_week

        # Créer le tableau de suivi par parcours pour la semaine spécifiée
        weekly_comparison_table = create_parcours_comparison_table(semaine, details_df1, planning_df)
    

        # Calculer le taux de suivi à partir du tableau de suivi
        taux_suivi = calculate_taux_suivi_from_table(weekly_comparison_table)
        weekly_details = details_df1[details_df1['semaine'] == semaine]
        completion_rates, weekly_completion_rate = calculate_completion_rates(weekly_details)


    

        # Calculer les indicateurs hebdomadaires
        heures_cumulees, surface_nettoyee, vitesse_moyenne, productivite_moyenne = calculate_weekly_indicators(details_df, semaine)

        # Calculer les coûts
        weekly_cost, hourly_cost, total_cost, utilization_rate = calculate_weekly_hourly_cost(heures_cumulees)
     
        # Sélection de la semaine
        semaine = selected_week

        # Filtrer les données pour la semaine sélectionnée
        filtered_alarm_details_df = filter_data_by_week(alarm_details_df, semaine)

        # Fonction pour catégoriser les heures
        def categorize_hour(hour):
            if 6 <= hour < 22:
                return 'Journée'
            else:
                return 'Nuit'

        # Convertir la colonne 'Apparition' en datetime si ce n'est pas déjà fait
        filtered_alarm_details_df['Apparition'] = pd.to_datetime(filtered_alarm_details_df['Apparition'])

        # Ajouter une colonne pour la catégorie (Journée/Nuit)
        filtered_alarm_details_df['Catégorie'] = filtered_alarm_details_df['Apparition'].dt.hour.map(categorize_hour)

        # Créer un sélecteur pour filtrer par catégorie
        categorie_filter = st.selectbox(
            "Filtrer par période",
            options=['Tous', 'Journée', 'Nuit']
        )

        # Filtrer les données en fonction de la sélection
        if categorie_filter != 'Tous':
            filtered_data = filtered_alarm_details_df[filtered_alarm_details_df['Catégorie'] == categorie_filter]
        else:
            filtered_data = filtered_alarm_details_df
    
       

        # Calculer le nombre total d'alertes pour la semaine
        total_alerts_week = len(filtered_data)

        # Calculer le temps de réalisation moyen des événements sur la semaine
        avg_resolution_time_week = filtered_data['Resolution Time'].mean()

        # Calculer les statistiques filtrées
        alert_count_by_description = filtered_data['Description'].value_counts().reset_index()
        alert_count_by_description.columns = ['Description', 'Alert Count']

        avg_resolution_time = filtered_data.groupby('Description')['Resolution Time'].mean().reset_index()
        avg_resolution_time.columns = ['Description', 'Avg Resolution Time (min)']

        alert_summary = pd.merge(alert_count_by_description, avg_resolution_time, on='Description')

   
        # Afficher les KPI côte à côte
        st.markdown("## **Indicateurs Hebdomadaires**")

        # Créer une disposition en grille de 3x2
        col1, col2, col3 = st.columns(3)
        col4, col5, col6 = st.columns(3)

        # Fonction helper pour créer un conteneur métrique
        def metric_container(label, value, delta=None):
            return f"""
            <div class="metric-container">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
                {f'<div class="metric-delta">{delta}</div>' if delta else ''}
            </div>
            """

        with col1:
            st.markdown(metric_container("Heures cumulées", f"{heures_cumulees:.2f} heures"), unsafe_allow_html=True)

        with col2:
            st.markdown(metric_container("Surfaces nettoyées cumulées", f"{surface_nettoyee:.2f} m²"), unsafe_allow_html=True)

        with col3:
            st.markdown(metric_container("Productivité moyenne", f"{productivite_moyenne:.2f} m²/h"), unsafe_allow_html=True)

        with col4:
            st.markdown(metric_container("Vitesse moyenne", f"{vitesse_moyenne:.2f} km/h"), unsafe_allow_html=True)

        with col5:
            st.markdown(metric_container("Coût total", f"{total_cost:.2f} €", f"Coût/h: {hourly_cost:.2f} €"), unsafe_allow_html=True)

        with col6:
            st.markdown(metric_container("Taux d'utilisation", f"{utilization_rate:.2f} %"), unsafe_allow_html=True)
    

        # Créer la jauge du taux de suivi
        fig_suivi = go.Figure(go.Indicator(
            mode="gauge+number",
            value=taux_suivi,
            title={'text': "Taux de suivi des parcours"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "white"},  # Couleur de l'indicateur
                'steps': [
                    {'range': [0, 40], 'color': "red"},
                    {'range': [40, 80], 'color': "orange"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': taux_suivi
                }
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
            title={'text': "Taux de réalisation des parcours"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "white"},  # Couleur de l'indicateur
                'steps': [
                    {'range': [0, 40], 'color': "red"},
                    {'range': [40, 80], 'color': "orange"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': weekly_completion_rate
                }
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
            st.subheader('Taux de réalisation des parcours')
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

        st.subheader('Taux de réalisation par parcours')
        completion_rates_df = completion_rates.reset_index()
        # Renommer les colonnes pour supprimer les caractères spéciaux
        completion_rates_df.columns = ['parcours', 'taux_completion']

        
        # Créer l'histogramme des taux de complétion par parcours
        completion_rates_df = completion_rates.reset_index()
        completion_rates_df.columns = ['parcours', 'taux_completion']

        fig_hist = px.bar(completion_rates_df, x='parcours', y='taux_completion',
                          title=f'Taux de réalisation par parcours (Semaine {semaine})',
                          labels={'parcours': 'Parcours', 'taux_completion': 'Taux de réalisation (%)'},
                          template='plotly_dark')

        # Ajouter une ligne horizontale à 90%
        fig_hist.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="Seuil de réalisation (90%)")

        # Ajuster la mise en page pour une meilleure lisibilité des noms de parcours
        fig_hist.update_layout(
            xaxis_tickangle=-45,
            xaxis_title="",
            yaxis=dict(range=[0, 100]),
            margin=dict(b=150)  # Augmenter la marge en bas pour les noms de parcours
        )

        # Afficher l'histogramme dans Streamlit
        st.plotly_chart(fig_hist, use_container_width=True)
    
        # Visualize the count of alerts and average resolution time by description
        st.subheader('Evènements Signalés')
        # Create two columns for the charts
        col1, col2 = st.columns(2)

        with col1:
            # Bar and line chart
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            fig.add_trace(
                go.Bar(x=alert_summary['Description'], y=alert_summary['Alert Count'], name="Nombre d'évènements"),
                secondary_y=False,
            )

            fig.add_trace(
                go.Scatter(x=alert_summary['Description'], y=alert_summary['Avg Resolution Time (min)'], name="Délai d'intervention moyen", mode='lines+markers'),
                secondary_y=True,
            )
    
            fig.update_layout(
                title_text=f"Nombre d'évènements par type et délai d'intervention moyen (Semaine {semaine}, {categorie_filter})",
                xaxis_title="Type d'évènements",
                template='plotly_dark'
            )

            fig.update_yaxes(title_text="Nombre d'évènements", secondary_y=False)
            fig.update_yaxes(title_text="Délai d'intervention (min)", secondary_y=True)

            st.plotly_chart(fig)

        with col2:
            # Pie chart
            fig_pie = create_pie_chart(alert_summary)
            fig_pie.update_layout(title_text=f"Répartition des évènements (Semaine {semaine}, {categorie_filter})")
            st.plotly_chart(fig_pie)

        st.subheader("Description des événements")
        st.dataframe(description_evenements,width=2000)
    # Mois
    # Mois
    elif period_selection == "Mois":
        mois_dict = {1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"}
        # Sélection du mois
        selected_month = st.selectbox("Sélectionnez le mois", options=range(1, 13), format_func=lambda x: mois_dict[x],key="month_selector")
        mois = selected_month
        details_df['mois'] = details_df['début'].dt.month
        # Filtrer les données pour le mois sélectionné
        details_df1['mois'] = details_df1['début'].dt.month
        
        monthly_details = details_df1[details_df1['mois'] == selected_month]
        # Calculer le taux de suivi pour le mois
        taux_suivi_moyen_mois = 0
        semaines_du_mois = monthly_details['semaine'].unique()
        for semaine in semaines_du_mois:
            weekly_comparison_table = create_parcours_comparison_table(semaine, details_df1, planning_df)
            taux_suivi_semaine = calculate_taux_suivi_from_table(weekly_comparison_table)
            taux_suivi_moyen_mois += taux_suivi_semaine
        taux_suivi_moyen_mois /= len(semaines_du_mois) if len(semaines_du_mois) > 0 else 1

        # Calculer le taux de réalisation pour le mois
        completion_rates, taux_realisation_moyen_mois = calculate_completion_rates(monthly_details)
        

        # Calcul des KPI mensuels
        heures_cumulees_mois, surface_nettoyee_mois, vitesse_moyenne_mois, productivite_moyenne_mois = calculate_monthly_indicators(details_df, mois)
        
        # Calculer le taux d'utilisation et le coût total mensuel
        jours_dans_le_mois = pd.Period(year=2024, month=selected_month, freq='M').days_in_month
        heures_prevues_par_jour = 3  # Ajustez selon vos besoins
        heures_prevues_mois = jours_dans_le_mois * heures_prevues_par_jour
        taux_utilisation_mois = (heures_cumulees_mois / heures_prevues_mois) * 100
         # Calculer le coût mensuel
        monthly_cost = 1600  # Coût mensuel fixe
        hourly_cost_month = monthly_cost / heures_cumulees_mois if heures_cumulees_mois > 0 else 0

        # Assurez-vous que cette ligne est présente et correcte
        filtered_alarm_details_df = alarm_details_df[alarm_details_df['mois'] == selected_month]
        # Fonction pour catégoriser les heures
        def categorize_hour(hour):
            if 6 <= hour < 22:
                return 'Journée'
            else:
                return 'Nuit'

        # Convertir la colonne 'Apparition' en datetime si ce n'est pas déjà fait
        filtered_alarm_details_df['Apparition'] = pd.to_datetime(filtered_alarm_details_df['Apparition'])

        # Ajouter une colonne pour la catégorie (Journée/Nuit)
        filtered_alarm_details_df['Catégorie'] = filtered_alarm_details_df['Apparition'].dt.hour.map(categorize_hour)

        # Créer un sélecteur pour filtrer par catégorie
        categorie_filter = st.selectbox(
            "Filtrer par période",
            options=['Tous', 'Journée', 'Nuit'],
            key="month_period_filter"
        )

        # Filtrer les données en fonction de la sélection
        if categorie_filter != 'Tous':
            filtered_data = filtered_alarm_details_df[filtered_alarm_details_df['Catégorie'] == categorie_filter]
        else:
            filtered_data = filtered_alarm_details_df


        # Calculer le nombre total d'alertes pour le mois
        total_alerts_month = len(filtered_data)

        # Calculer le temps de réalisation moyen des événements sur le mois
        avg_resolution_time_month = filtered_data['Resolution Time'].mean()

        # Calculer le temps de réalisation moyen des événements sur le mois
        avg_resolution_time_month = filtered_data['Resolution Time'].mean()
        # Calculer les statistiques filtrées
        alert_count_by_description = filtered_data['Description'].value_counts().reset_index()
        alert_count_by_description.columns = ['Description', 'Alert Count']

        avg_resolution_time = filtered_data.groupby('Description')['Resolution Time'].mean().reset_index()
        avg_resolution_time.columns = ['Description', 'Avg Resolution Time (min)']

        alert_summary = pd.merge(alert_count_by_description, avg_resolution_time, on='Description')


        # Affichage des KPI pour le mois
        st.markdown("### Indicateurs Mensuels")

        col1, col2, col3, col4 = st.columns(4)
        col5, col6, col7, col8 = st.columns(4)
        with col1:
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-label">Heures cumulées (Mois)</div>
                    <div class="metric-value">{heures_cumulees_mois:.2f} heures</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-label">Surfaces nettoyées cumulées (Mois)</div>
                    <div class="metric-value">{surface_nettoyee_mois:.2f} m²</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-label">Productivité moyenne (Mois)</div>
                    <div class="metric-value">{productivite_moyenne_mois:.2f} m²/h</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col4:
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-label">Vitesse moyenne (Mois)</div>
                    <div class="metric-value">{vitesse_moyenne_mois:.2f} km/h</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col5:
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-label">Nombre d'événements signalés (Mois)</div>
                    <div class="metric-value">{total_alerts_month}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col6:
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-label">Délai d’intervention moyen suite aux évènements (Mois)</div>
                    <div class="metric-value">{avg_resolution_time_month:.2f} min</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col7:
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-label">Taux d'utilisation (Mois)</div>
                    <div class="metric-value">{taux_utilisation_mois:.2f}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col8:
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-label">Coût total (Mois)</div>
                    <div class="metric-value">{monthly_cost:.2f} €</div>
                    <div class="metric-delta">Coût/h: {hourly_cost_month:.2f} €</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        
        # Créer la jauge du taux de suivi
        fig_suivi = go.Figure(go.Indicator(
            mode="gauge+number",
            value=taux_suivi_moyen_mois,
            title={'text': "Taux de suivi des parcours"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "white"},  # Couleur de l'indicateur
                'steps': [
                    {'range': [0, 40], 'color': "red"},
                    {'range': [40, 80], 'color': "orange"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': taux_suivi_moyen_mois
                }
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
            value=taux_realisation_moyen_mois,
            title={'text': "Taux de réalisation des parcours"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "white"},  # Couleur de l'indicateur
                'steps': [
                    {'range': [0, 40], 'color': "red"},
                    {'range': [40, 80], 'color': "orange"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': taux_realisation_moyen_mois
                }
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
            st.subheader('Taux de réalisation des parcours')
            st.plotly_chart(fig_completion)

        # Visualize the count of alerts and average resolution time by description
        st.subheader('Evènements Signalés')
        # Create two columns for the charts
        col1, col2 = st.columns(2)

        with col1:
            # Bar and line chart
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            fig.add_trace(
                go.Bar(x=alert_summary['Description'], y=alert_summary['Alert Count'], name="Nombre d'évènements"),
                secondary_y=False,
            )

            fig.add_trace(
                go.Scatter(x=alert_summary['Description'], y=alert_summary['Avg Resolution Time (min)'], name="Délai d'intervention moyen", mode='lines+markers'),
                secondary_y=True,
            )

            fig.update_layout(
                title_text=f"Nombre d'évènements par type et délai d'intervention moyen ({categorie_filter})",
                xaxis_title="Type d'évènements",
                template='plotly_dark'
            )

            fig.update_yaxes(title_text="Nombre d'évènements", secondary_y=False)
            fig.update_yaxes(title_text="Délai d'intervention (min)", secondary_y=True)

            st.plotly_chart(fig)

        with col2:
            # Pie chart
            fig_pie = create_pie_chart(alert_summary)
            fig_pie.update_layout(title_text=f"Répartition des évènements ({categorie_filter})")
            st.plotly_chart(fig_pie)



       

        # Create the monthly alerts comparison chart
        st.subheader("Comparaison du nombre d'événements signalés par mois")

        # Create a DataFrame with all months
        all_months = pd.DataFrame({
            'mois': range(1, 13),
            'Mois': [mois_dict[i] for i in range(1, 13)]
        })

        # Get the count of alerts for each month
        monthly_alerts = alarm_details_df.groupby('mois')['Description'].count().reset_index()

        # Merge all months with the actual data
        monthly_alerts = all_months.merge(monthly_alerts, on='mois', how='left')

        # Fill NaN values with 0 for months without data
        monthly_alerts['Description'] = monthly_alerts['Description'].fillna(0)

        # Create the bar chart
        fig_monthly_alerts = px.bar(monthly_alerts, x='Mois', y='Description', 
                                    title='Nombre d\'événements signalés par mois',
                                    template='plotly_dark')

        fig_monthly_alerts.update_layout(
            xaxis_title="Mois", 
            yaxis_title="Nombre d'événements",
            xaxis={'categoryorder':'array', 'categoryarray': [mois_dict[i] for i in range(1, 13)]}
        )

        st.plotly_chart(fig_monthly_alerts)
        st.subheader("Description des événements")
        st.dataframe(description_evenements,width=2000)
        st.subheader("Comparatif des taux de suivi par mois")
        # Récupérer les données de taux de suivi pour tous les mois
        all_months_taux_suivi = []
        for month in range(1, 13):
            monthly_details = details_df1[details_df1['mois'] == month]
            semaines_du_mois = monthly_details['semaine'].unique()
            weekly_taux_suivi = []
            for semaine in semaines_du_mois:
                weekly_comparison_table = create_parcours_comparison_table(semaine, details_df1, planning_df)
                taux_suivi_semaine = calculate_taux_suivi_from_table(weekly_comparison_table)
                weekly_taux_suivi.append(taux_suivi_semaine)
            taux_suivi_moyen_mois = sum(weekly_taux_suivi) / len(weekly_taux_suivi) if weekly_taux_suivi else 0
            all_months_taux_suivi.append(taux_suivi_moyen_mois)

        # Créer l'histogramme des taux de suivi par mois
        fig_taux_suivi = px.bar(x=list(mois_dict.values()), y=all_months_taux_suivi,
                               title='Taux de suivi des parcours par mois',
                               labels={'x': 'Mois', 'y': 'Taux de suivi (%)'},
                               template='plotly_dark')
        # Ajuster la mise en page pour une meilleure lisibilité des noms de parcours
        fig_taux_suivi.update_layout(
            xaxis_tickangle=-45,
            xaxis_title="",
            yaxis=dict(range=[0, 100]),
            margin=dict(b=150)  # Augmenter la marge en bas pour les noms de parcours
        )
        st.plotly_chart(fig_taux_suivi)
        
    

        # Bar chart for route completion rates over several months
        st.subheader("Taux de réalisation des parcours")

        # Définir l'ordre des parcours
        ordre_parcours = [
            'T D centre',
            'L centre',
            'L novotel',
            'L brioche',
            'L air france',
            'T F af',
            'T F brioche'

        ]

        # Créer l'histogramme des taux de complétion par parcours
        completion_rates_df = completion_rates.reset_index()
        completion_rates_df.columns = ['parcours', 'taux_completion']

        # Filtrer et trier le DataFrame selon l'ordre spécifié
        completion_rates_df = completion_rates_df[completion_rates_df['parcours'].isin(ordre_parcours)]
        completion_rates_df['parcours'] = pd.Categorical(completion_rates_df['parcours'], categories=ordre_parcours, ordered=True)
        completion_rates_df = completion_rates_df.sort_values('parcours')

        fig_hist = px.bar(completion_rates_df, x='parcours', y='taux_completion',
                          title=f'Taux de réalisation par parcours ({"Semaine " + str(semaine) if period_selection == "Semaine" else "Mois " + mois_dict[selected_month]})',
                          labels={'parcours': 'Parcours', 'taux_completion': 'Taux de réalisation (%)'},
                          template='plotly_dark',
                          category_orders={"parcours": ordre_parcours})

        # Ajouter une ligne horizontale à 90%
        fig_hist.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="Seuil de réalisation (90%)")

        # Ajuster la mise en page pour une meilleure lisibilité des noms de parcours et fixer l'échelle de 0 à 100%
        fig_hist.update_layout(
            xaxis_tickangle=-45,
            xaxis_title="",
            yaxis=dict(range=[0, 100]),  # Fixer l'échelle de l'axe y de 0 à 100%
            margin=dict(b=150)  # Augmenter la marge en bas pour les noms de parcours
        )

        # Afficher l'histogramme dans Streamlit
        st.plotly_chart(fig_hist, use_container_width=True)

        # Calculer les taux de réalisation pour tous les mois
        all_months_completion_rates = []
        for month in range(1, 13):
            monthly_data = details_df1[details_df1['mois'] == month]
            _, taux_realisation = calculate_completion_rates(monthly_data)
            all_months_completion_rates.append(taux_realisation)

        # Créer un DataFrame pour l'histogramme comparatif
        comparative_df = pd.DataFrame({
            'Mois': list(mois_dict.values()),
            'Taux de réalisation': all_months_completion_rates
        })

        # Créer l'histogramme comparatif
        fig_comparative = px.bar(comparative_df, x='Mois', y='Taux de réalisation',
                                 title='Comparatif des taux de réalisation des parcours par mois',
                                 labels={'Taux de réalisation': 'Taux de réalisation (%)'},
                                 template='plotly_dark')

        # Ajouter une ligne horizontale à 90%
        fig_comparative.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="Seuil de réalisation (90%)")

        # Ajuster la mise en page
        fig_comparative.update_layout(
            xaxis_title="",
            yaxis=dict(range=[0, 100]),  # Fixer l'échelle de l'axe y de 0 à 100%
            margin=dict(b=50)
        )

        # Afficher l'histogramme comparatif dans Streamlit
        st.subheader("Comparatif des taux de réalisation par mois")
        st.plotly_chart(fig_comparative, use_container_width=True)

    if 'current_app' not in st.session_state:
        st.session_state.current_app = "RQUARTZ T2F"

    st.subheader("Actions correctives")

    # Connexion à Supabase avec les informations de connexion
    url = "https://jienhfjzykyjwpihuvcl.supabase.co"  # Remplace par l'URL de ton projet Supabase
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImppZW5oZmp6eWt5andwaWh1dmNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjU5NTE0NjYsImV4cCI6MjA0MTUyNzQ2Nn0.uRexXku6cZCo4qPT_coXJtL3s31-lh_P9J469FhLxvk"  # Remplace par ta clé API
    supabase: Client = create_client(url, key)
    # Fonction pour uploader un fichier dans le bucket Supabase
    def upload_file_to_bucket(file, action_id):
        try:
            # Créer un chemin unique pour le fichier dans le bucket
            file_path = f"pdf_uploads/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.name}"
        
            # Lire le fichier
            file_content = file.read()

            # Uploader le fichier dans le bucket Supabase
            response = supabase.storage().from_('IMON').upload(file_path, file_content)
        
            if response.status_code == 200:
                st.success(f"Le fichier a été uploadé avec succès pour l'action {action_id}")
                return file_path  # Retourne le chemin du fichier dans le bucket
            else:
                st.error(f"Erreur lors de l'upload du fichier : {response.json()}")
                return None
        except Exception as e:
            st.error(f"Erreur lors de l'upload : {e}")
            return None
    def save_pdf_url_in_db(action_id, file_url):
        try:
            supabase.table('actions_correctives').update({"pdf_url": file_url}).eq("id", action_id).execute()
            return True
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde du fichier PDF : {e}")
            return False

   # Fonction pour charger les actions correctives depuis Supabase sans changer les noms des colonnes
    def load_actions_correctives():
        try:
            response = supabase.table('actions_correctives').select('*').execute()
            data = response.data
            if not data:
                # Si la table est vide, on retourne un DataFrame vide avec les bonnes colonnes
                return pd.DataFrame(columns=['action_corrective', 'date_ajout', 'delai_intervention', 'responsable_action', 'statut', 'commentaires'])
            df = pd.DataFrame(data)

            # Convertir les dates
            df['date_ajout'] = pd.to_datetime(df['date_ajout']).dt.date
            df['delai_intervention'] = pd.to_datetime(df['delai_intervention']).dt.date

            return df
        except Exception as e:
            st.error(f"Erreur lors du chargement des données : {e}")
            return pd.DataFrame(columns=['action_corrective', 'date_ajout', 'delai_intervention', 'responsable_action', 'statut', 'commentaires'])

    # Charger les données à chaque lancement de l'application
    st.session_state.actions_correctives_T2F = load_actions_correctives()

    def save_actions_correctives(df):
        try:
            for index, row in df.iterrows():
                # Convertir les dates si elles ne sont pas déjà en format datetime
                if isinstance(row['date_ajout'], str):
                    row['date_ajout'] = pd.to_datetime(row['date_ajout'], errors='coerce').date()
                if isinstance(row['delai_intervention'], str):
                    row['delai_intervention'] = pd.to_datetime(row['delai_intervention'], errors='coerce').date()

                # Préparer les données à sauvegarder
                data_to_save = {
                    'action_corrective': row['action_corrective'],
                    'date_ajout': row['date_ajout'].strftime('%Y-%m-%d') if pd.notna(row['date_ajout']) else None,
                    'delai_intervention': row['delai_intervention'].strftime('%Y-%m-%d') if pd.notna(row['delai_intervention']) else None,
                    'responsable_action': row['responsable_action'],
                    'statut': row['statut'],
                    'commentaires': row['commentaires']
                }

                if 'id' in row and pd.notna(row['id']):
                    data_to_save['id'] = int(row['id'])  # Convertir l'ID en entier
                    supabase.table('actions_correctives').update(data_to_save).eq('id', data_to_save['id']).execute()
                else:
                    supabase.table('actions_correctives').insert(data_to_save).execute()

            return True
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde des données : {e}")
            return False



    # Fonction pour convertir les colonnes de date en datetime avant de les utiliser dans le data_editor
    def prepare_df_for_editing(df):
        try:
            # Assurer que les colonnes de dates sont bien en format datetime.date
            df['date_ajout'] = pd.to_datetime(df['date_ajout'], errors='coerce').dt.date
            df['delai_intervention'] = pd.to_datetime(df['delai_intervention'], errors='coerce').dt.date
            return df
        except Exception as e:
            st.error(f"Erreur lors de la conversion des colonnes de date : {e}")
            return df

    # Initialiser le state si nécessaire
    if 'actions_correctives_T2F' not in st.session_state:
        st.session_state.actions_correctives_T2F = load_actions_correctives()

    # Préparer le DataFrame pour l'édition en s'assurant que les colonnes de date sont bien converties
    st.session_state.actions_correctives_T2F = prepare_df_for_editing(st.session_state.actions_correctives_T2F)

    if 'editing_T2F' not in st.session_state:
        st.session_state.editing_T2F = False

    # Basculer entre mode édition et visualisation
    def toggle_edit_mode_T2F():
        st.session_state.editing_T2F = not st.session_state.editing_T2F

    st.button("Modifier les actions correctives" if not st.session_state.editing_T2F else "Terminer l'édition", 
              on_click=toggle_edit_mode_T2F, key='toggle_edit_T2F')

    if st.session_state.editing_T2F:
        # Mode d'édition avec les dates converties en format approprié
        edited_df = st.data_editor(
            st.session_state.actions_correctives_T2F,
            num_rows="dynamic",
            column_config={
                "action_corrective": st.column_config.TextColumn(
                    "Action corrective",
                    max_chars=100,
                    width="large",
                ),
                "date_ajout": st.column_config.DateColumn(
                    "date_ajout",
                    format="DD/MM/YYYY",
                    width="medium",
                ),
                "delai_intervention": st.column_config.DateColumn(
                    "delai_intervention",
                    format="DD/MM/YYYY",
                    width="medium",
                ),
                "responsable_action": st.column_config.TextColumn(
                    "responsable_action",
                    max_chars=50,
                    width="medium",
                ),
                "statut": st.column_config.SelectboxColumn(
                    "statut",
                    options=['En cours', 'Terminé', 'En retard'],
                    width="small",
                ),
                "commentaires": st.column_config.TextColumn(
                    "commentaires",
                    max_chars=200,
                    width="large",
                ),
            },
            hide_index=True,
            width=2000,
            key='data_editor_T2F'
        )
        # Ajoutez un bouton d'upload dans chaque ligne pour chaque action corrective
        for index, row in edited_df.iterrows():
            file_to_upload = st.file_uploader(f"Uploader un fichier PDF pour {row['action_corrective']}", type="pdf", key=f"file_uploader_{row['id']}")
        
            if file_to_upload:
                # Uploader le fichier et obtenir l'URL
                file_path = upload_file_to_bucket(file_to_upload, row['id'])
                if file_path:
                    # Générer l'URL du fichier
                    file_url = f"https://{url}/storage/v1/object/public/{file_path}"
                
                    # Sauvegarder l'URL dans la base de données
                    if save_pdf_url_in_db(row['id'], file_url):
                        st.success(f"Le fichier PDF pour l'action corrective {row['action_corrective']} a été enregistré avec succès.")

        if st.button("Sauvegarder les modifications", key='save_T2F'):
            st.session_state.actions_correctives_T2F = edited_df
            if save_actions_correctives(edited_df):
                st.success("Actions sauvegardées avec succès.")
            st.session_state.editing_T2F = False
    else:
        # Mode de visualisation
        st.dataframe(st.session_state.actions_correctives_T2F, width=2000)

    def reload_page():
       raise RerunException(rerun_data=None)

    # Interface pour recharger les données
    if st.button("Recharger les données"):
       reload_page()


    
if __name__ == '__main__':
    main()
