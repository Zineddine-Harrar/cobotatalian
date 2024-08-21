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

    def calculate_average_resolution_time(df):
        df['Resolution Time'] = (df['Retour'] - df['Apparition']).dt.total_seconds() / 60
        avg_resolution_time = df.groupby('Description')['Resolution Time'].mean().reset_index()
        avg_resolution_time.columns = ['Description', 'Avg Resolution Time (min)']
        return avg_resolution_time
    def create_pie_chart(alert_summary):
        fig_pie = px.pie(alert_summary, values='Alert Count', names='Description', 
                         title='Répartition des évènements',
                         template='plotly_dark',
                         hole=0.3)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        return fig_pie

    # Variables pour le calcul du taux d'utilisation
    working_hours_per_day = 6  # Nombre d'heures de travail prévues par jour
    working_days_per_week = 7  # Nombre de jours de travail prévus par semaine

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
        
    # Load the dataset with appropriate header row
    file_path = "DATASET/ALERTE/T2F/Alerte T2F  19-08.xlsx"
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

    st.title('Indicateurs de Suivi des Parcours du RQUARTZ T2F')

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

    period_selection = st.radio("Sélectionnez la période à analyser", ["Semaine", "Mois"])
    if period_selection == "Semaine":
        selected_week = st.selectbox("Sélectionnez le numéro de la semaine", options=list(week_options.keys()), format_func=lambda x: f"Semaine {x} ({week_options[x].strftime('%d/%m/%Y')})")

        # Sélection de la semaine
        semaine = selected_week

        # Créer le tableau de suivi par parcours pour la semaine spécifiée
        weekly_comparison_table = create_parcours_comparison_table(semaine, details_df1, planning_df)
    

        # Calculer le taux de suivi à partir du tableau de suivi
        taux_suivi = calculate_taux_suivi_from_table(weekly_comparison_table)

        # Calculer le taux de complétion hebdomadaire
        weekly_completion_rate, completion_rates = calculate_weekly_completion_rate(details_df1, semaine)

    

        # Calculer les indicateurs hebdomadaires
        heures_cumulees, surface_nettoyee, vitesse_moyenne, productivite_moyenne = calculate_weekly_indicators(details_df, semaine)

        # Calculer les coûts
        weekly_cost, hourly_cost, total_cost, utilization_rate = calculate_weekly_hourly_cost(heures_cumulees)
     
        # Filter alarm data by the selected week
        filtered_alarm_details_df = filter_data_by_week(alarm_details_df, semaine)

        # Calculate the count of alerts by description
        alert_count_by_description = filtered_alarm_details_df['Description'].value_counts().reset_index()
        alert_count_by_description.columns = ['Description', 'Alert Count']

        # Calculate average resolution time by description
        avg_resolution_time = calculate_average_resolution_time(filtered_alarm_details_df)

        # Merge alert count and average resolution time
        alert_summary = pd.merge(alert_count_by_description, avg_resolution_time, on='Description')    # Afficher les KPI côte à côte
   
        # Afficher les KPI côte à côte
        st.markdown("## **Indicateurs Hebdomadaires**")

        col1, col2, col3, col4, col5, col6 = st.columns(6)

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
                    <div class="metric-label">Surfaces nettoyées cumulées</div>
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

        with col5:
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-label">Coût total</div>
                    <div class="metric-value">{total_cost:.2f} €</div>
                    <div class="metric-delta">Coût/h: {hourly_cost:.2f} €</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col6:
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-label">Taux d'utilisation</div>
                    <div class="metric-value">{utilization_rate:.2f} %</div>
                </div>
                """,
                unsafe_allow_html=True
            
            )
    

        # Créer la jauge du taux de suivi
        fig_suivi = go.Figure(go.Indicator(
            mode="gauge+number",
            value=taux_suivi,
            title={'text': "Taux de suivi des parcours"},
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
            title={'text': "Taux de réalisation des parcours"},
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

    
        completion_rates_df = completion_rates.reset_index()
        # Renommer les colonnes pour supprimer les caractères spéciaux
        completion_rates_df.columns = ['parcours', 'taux_completion']

        
        # Transformer en DataFrame pour Plotly
        completion_rates_df = completion_rates.reset_index()
        completion_rates_df.columns = ['parcours', 'taux_completion']

        # Créer l'histogramme des taux de complétion par parcours
        fig_hist = px.bar(completion_rates_df, x='parcours', y='taux_completion',
                      title='Taux de réalisation par parcours ',
                      labels={'parcours': 'Parcours', 'taux_completion': 'Taux de réalisation (%)'},
                      template='plotly_dark')

        # Afficher l'histogramme dans Streamlit
        st.plotly_chart(fig_hist)
    
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
                title_text=" Nombre d'évènements par type et délai d'intervention moyen ",
                xaxis_title="Type d'évènements",
                template='plotly_dark'
            )

            fig.update_yaxes(title_text="Nombre d'évènements", secondary_y=False)
            fig.update_yaxes(title_text="Délai d'intervention (min)", secondary_y=True)

            st.plotly_chart(fig)

        with col2:
            # Pie chart
            fig_pie = create_pie_chart(alert_summary)
            st.plotly_chart(fig_pie)
        st.subheader("Description des événements")
        st.dataframe(description_evenements,width=2000)
    # Mois
    # Mois
    elif period_selection == "Mois":
        mois_dict = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}
        # Sélection du mois
        selected_month = st.selectbox("Sélectionnez le mois", options=range(1, 13), format_func=lambda x: datetime(2024, x, 1).strftime("%B"))

        # Filtrer les données pour le mois sélectionné
        details_df1['mois'] = details_df1['début'].dt.month
        monthly_details = details_df1[details_df1['mois'] == selected_month]
        # Récupérer toutes les semaines du mois sélectionné
        semaines_du_mois = monthly_details['semaine'].unique()

        # Initialiser des listes pour stocker les taux de suivi et de réalisation hebdomadaires
        weekly_taux_suivi = []
        weekly_completion_rates = []

        # Calculer le taux de suivi et de réalisation pour chaque semaine du mois
        for semaine in semaines_du_mois:
            # Créer le tableau de suivi par parcours pour la semaine spécifiée
            weekly_comparison_table = create_parcours_comparison_table(semaine, details_df1, planning_df)
    
            # Calculer le taux de suivi à partir du tableau de suivi
            taux_suivi_semaine = calculate_taux_suivi_from_table(weekly_comparison_table)
            weekly_taux_suivi.append(taux_suivi_semaine)

            # Calculer le taux de réalisation hebdomadaire
            weekly_completion_rate, _ = calculate_weekly_completion_rate(details_df1, semaine)
            weekly_completion_rates.append(weekly_completion_rate)

        # Calculer la moyenne des taux de suivi pour le mois
        taux_suivi_moyen_mois = sum(weekly_taux_suivi) / len(weekly_taux_suivi) if weekly_taux_suivi else 0

        # Calculer la moyenne des taux de réalisation pour le mois
        taux_realisation_moyen_mois = sum(weekly_completion_rates) / len(weekly_completion_rates) if weekly_completion_rates else 0

        # Calcul des KPI mensuels

        # Heures cumulées et surfaces nettoyées sur le mois
        heures_cumulees_mois = monthly_details['durée[mn]'].sum() / 60  # Convertir les minutes en heures
        surface_nettoyee_mois = monthly_details['surfacepropre_[mq]'].sum()

        # Moyennes mensuelles pour la productivité et la vitesse
        vitesse_moyenne_mois = monthly_details['vitesse_moyenne[km/h]'].mean()
        productivite_moyenne_mois = monthly_details['productivitéhoraire_[mq/h]'].mean()

        # Calcul du nombre d'événements signalés cumulés sur le mois
        filtered_alarm_details_df_month = alarm_details_df[alarm_details_df['mois'] == selected_month]
        print("filtered_alarm_details_df_month:")
        print(filtered_alarm_details_df_month)
        total_alerts_month = len(filtered_alarm_details_df_month)
    
        # Calcul du temps de réalisation moyen des événements sur le mois
        avg_resolution_time_month = filtered_alarm_details_df_month['Resolution Time'].mean()

        # Calculate the count of alerts by description
        alert_count_by_description = filtered_alarm_details_df_month['Description'].value_counts().reset_index()
        alert_count_by_description.columns = ['Description', 'Alert Count']
        print("alert_count_by_description:")
        print(alert_count_by_description)

        # Calculate average resolution time by description
        avg_resolution_time = calculate_average_resolution_time(filtered_alarm_details_df_month)
        print("avg_resolution_time:")
        print(avg_resolution_time)
        st.dataframe(filtered_alarm_details_df_month)

        # Merge alert count and average resolution time
        alert_summary = pd.merge(alert_count_by_description, avg_resolution_time, on='Description')
        print("alert_summary:")
        print(alert_summary)

        # Affichage des KPI pour le mois
        st.markdown("### Indicateurs Mensuels")

        col1, col2, col3, col4, col5, col6 = st.columns(6)

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
                    <div class="metric-label">Temps de réalisation moyen (Mois)</div>
                    <div class="metric-value">{avg_resolution_time_month:.2f} min</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Créer la jauge du taux de suivi
        fig_suivi = go.Figure(go.Indicator(
            mode="gauge+number",
            value=taux_suivi_moyen_mois,
            title={'text': "Taux de suivi des parcours"},
            gauge={
                'axis': {'range': [None, 100]},
                'steps': [
                    {'range': [0, 50], 'color': "orange"},
                    {'range': [50, 100], 'color': "green"}],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': taux_suivi_moyen_mois}
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
                'steps': [
                    {'range': [0, 50], 'color': "orange"},
                    {'range': [50, 100], 'color': "green"}],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': taux_realisation_moyen_mois}
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
                title_text=f"Nombre d'évènements par type et délai d'intervention moyen (Mois {mois_dict[selected_month]})",
                xaxis_title="Type d'évènements",
                template='plotly_dark'
            )

            fig.update_yaxes(title_text="Nombre d'évènements", secondary_y=False)
            fig.update_yaxes(title_text="Délai d'intervention (min)", secondary_y=True)
    
            st.plotly_chart(fig)

        with col2:
            # Pie chart
            fig_pie = create_pie_chart(alert_summary)
            fig_pie.update_layout(
                title_text=f"Répartition des évènements (Mois {mois_dict[selected_month]})",
                template='plotly_dark'
            )
            st.plotly_chart(fig_pie)
    
if __name__ == '__main__':
    main()
   
