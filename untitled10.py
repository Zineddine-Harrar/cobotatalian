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
            overflow: hidden;  /* Cache le débordement */
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
        </style>
        <script>
        function adjustFontSize() {
            document.querySelectorAll('.metric-container').forEach(container => {
                const label = container.querySelector('.metric-label');
                const value = container.querySelector('.metric-value');
                const delta = container.querySelector('.metric-delta');
        
                let fontSize = 2.6;
                value.style.fontSize = `${fontSize}em`;
        
                while (container.scrollHeight > container.clientHeight && fontSize > 1) {
                    fontSize -= 0.1;
                    value.style.fontSize = `${fontSize}em`;
                }
        
                // Ajuster la taille du label et du delta proportionnellement
                label.style.fontSize = `${fontSize * 0.615}em`;  // 1.6 / 2.6 ≈ 0.615
                if (delta) {
                    delta.style.fontSize = `${fontSize * 0.5}em`;  // 1.3 / 2.6 ≈ 0.5
                }
            });
        }

        // Exécuter l'ajustement au chargement et au redimensionnement de la fenêtre
        window.addEventListener('load', adjustFontSize);
        window.addEventListener('resize', adjustFontSize);
        </script>
        """,
        unsafe_allow_html=True
    )

    # Charger les fichiers CSV
    planning_df = pd.read_csv('ECOBOT40.csv', delimiter=';', encoding='ISO-8859-1')
    details_df = pd.read_csv('DATASET/ECOBOT40/19-08.csv', encoding='ISO-8859-1', delimiter=';', on_bad_lines='skip')

    # Nettoyer les colonnes dans details_df0
    details_df.columns = details_df.columns.str.replace('\r\n', '').str.strip()
    details_df.columns = details_df.columns.str.replace(' ', '_').str.lower()

    # Convertir la colonne task_start_time en type datetime
    details_df['task_start_time'] = pd.to_datetime(details_df['task_start_time'])

    # Utiliser l'accessor .dt pour obtenir le nom du jour
    details_df['jour'] = details_df['task_start_time'].dt.day_name()
    # Ajouter la colonne semaine
    details_df['semaine'] = details_df['task_start_time'].dt.isocalendar().week
    details_df['date'] = details_df['task_start_time'].dt.date
    details_df['mois'] = details_df['task_start_time'].dt.month
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
    # Fonction pour calculer le taux de complétion
    def calculate_completion_rates(details_df, threshold=90):
        completion_rates = details_df.groupby('cleaning_plan')['task_completion_(%)'].mean()
        parcours_realises = (completion_rates >= threshold).sum()
        total_parcours = len(completion_rates)
        taux_realisation = (parcours_realises / total_parcours) * 100 if total_parcours > 0 else 0
        return completion_rates, taux_realisation

    # Fonction pour calculer les indicateurs mensuels
    def calculate_monthly_indicators(details_df, mois):
        monthly_details = details_df[details_df['mois'] == mois]
        heures_cumulees_mois = monthly_details['total_time_(h)'].sum()
        surface_nettoyee_mois = monthly_details['actual_cleaning_area(?)'].sum()
        productivite_moyenne_mois = monthly_details['work_efficiency_(?/h)'].mean()
        return heures_cumulees_mois, surface_nettoyee_mois, productivite_moyenne_mois
        
    # Fonction pour calculer les indicateurs hebdomadaires
    def calculate_weekly_indicators(details_df, semaine):
        weekly_details = details_df[details_df['semaine'] == semaine]
        heures_cumulees = weekly_details['total_time_(h)'].sum()
        surface_nettoyee = weekly_details['actual_cleaning_area(?)'].sum()
        productivite_moyenne = weekly_details['work_efficiency_(?/h)'].mean()
        return heures_cumulees, surface_nettoyee, productivite_moyenne

     # Variables pour le calcul du taux d'utilisation
    working_hours_per_day = 3  # Nombre d'heures de travail prévues par jour
    working_days_per_week = 7  # Nombre de jours de travail prévus par semaine
    def calculate_weekly_hourly_cost(heures_cumulees, monthly_cost=840, weeks_per_month=4):
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
    if 'period_selection' not in st.session_state:
        st.session_state['period_selection'] = "Semaine"

    period_selection = st.selectbox(
        "Sélectionnez la période à analyser",
        ["Semaine", "Mois"],
        index=["Semaine", "Mois"].index(st.session_state['period_selection'])
    )

    st.session_state['period_selection'] = period_selection
    if period_selection == "Semaine":
        # Afficher le sélecteur de semaine avec les dates
        selected_week = st.selectbox("Sélectionnez le numéro de la semaine", options=list(week_options.keys()), format_func=lambda x: f"Semaine {x} ({week_options[x].strftime('%d/%m/%Y')})")

        # Sélection de la semaine
        semaine = selected_week

        weekly_comparison_table = create_parcours_comparison_table(semaine, details_df1, planning_df)
        taux_suivi = calculate_taux_suivi_from_table(weekly_comparison_table)
        completion_rates, weekly_completion_rate = calculate_weekly_completion_rate(details_df1, semaine)
        heures_cumulees, surface_nettoyee, productivite_moyenne = calculate_weekly_indicators(details_df, semaine)
        # Calculer les coûts
        weekly_cost, hourly_cost, total_cost, utilization_rate = calculate_weekly_hourly_cost(heures_cumulees)
        st.markdown("## **Indicateurs Hebdomadaires**")
        col1, col2, col3, col4, col5 = st.columns(5)

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
                    <div class="metric-label">Coût total</div>
                    <div class="metric-value">{total_cost:.2f} €</div>
                    <div class="metric-delta">Coût/h: {hourly_cost:.2f} €</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col5:
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
    
    elif period_selection == "Mois":
        # Nouveau code pour la vue mensuelle
        mois_dict = {1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin", 
                     7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"}
    
        # Sélection du mois
        selected_month = st.selectbox("Sélectionnez le mois", options=range(1, 13), 
                                      format_func=lambda x: mois_dict[x])

        # Filtrer les données pour le mois sélectionné
        details_df1['mois'] = details_df1['task_start_time'].dt.month
        monthly_details = details_df1[details_df1['mois'] == selected_month]
        details_df['mois'] = details_df['task_start_time'].dt.month
        # Calculer les indicateurs mensuels
        heures_cumulees_mois, surface_nettoyee_mois, productivite_moyenne_mois = calculate_monthly_indicators(details_df, selected_month)  

        # Calculer le taux de suivi pour le mois
        taux_suivi_moyen_mois = 0
        semaines_du_mois = monthly_details['semaine'].unique()
        for semaine in semaines_du_mois:
            weekly_comparison_table = create_parcours_comparison_table(semaine, details_df1, planning_df)
            taux_suivi_semaine = calculate_taux_suivi_from_table(weekly_comparison_table)
            taux_suivi_moyen_mois += taux_suivi_semaine
        taux_suivi_moyen_mois /= len(semaines_du_mois) if len(semaines_du_mois) > 0 else 1

        # Calculer le taux de réalisation pour le mois
        completion_rates_month, taux_realisation_moyen_mois = calculate_completion_rates(monthly_details)

        # Calculer le taux d'utilisation et le coût total mensuel
        jours_dans_le_mois = pd.Period(year=2024, month=selected_month, freq='M').days_in_month
        heures_prevues_par_jour = 3  # Ajustez selon vos besoins
        heures_prevues_mois = jours_dans_le_mois * heures_prevues_par_jour
        taux_utilisation_mois = (heures_cumulees_mois / heures_prevues_mois) * 100

        # Calculer le coût mensuel
        monthly_cost = 840  # Coût mensuel fixe
        hourly_cost_month = monthly_cost / heures_cumulees_mois if heures_cumulees_mois > 0 else 0

        # Afficher les indicateurs mensuels
        st.markdown("## **Indicateurs Mensuels**")
        col1, col2, col3, col4, col5 = st.columns(5)

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
                    <div class="metric-label">Surface nettoyée (Mois)</div>
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
                    <div class="metric-label">Coût total (Mois)</div>
                    <div class="metric-value">{monthly_cost:.2f} €</div>
                    <div class="metric-delta">Coût/h: {hourly_cost_month:.2f} €</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col5:
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-label">Taux d'utilisation (Mois)</div>
                    <div class="metric-value">{taux_utilisation_mois:.2f} %</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Créer les jauges pour le taux de suivi et le taux de réalisation mensuel
        fig_suivi_mois = go.Figure(go.Indicator(
            mode="gauge+number",
            value=taux_suivi_moyen_mois,
            title={'text': "Taux de Suivi Mensuel"},
            gauge={
                'axis': {'range': [None, 100]},
                'steps': [
                    {'range': [0, 50], 'color': "orange"},
                    {'range': [50, 100], 'color': "green"}],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': taux_suivi_moyen_mois}
            }
        ))
    
        fig_completion_mois = go.Figure(go.Indicator(
            mode="gauge+number",
            value=taux_realisation_moyen_mois,
            title={'text': "Taux de Réalisation Mensuel"},
            gauge={
                'axis': {'range': [None, 100]},
                'steps': [
                    {'range': [0, 50], 'color': "orange"},
                    {'range': [50, 100], 'color': "green"}],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': taux_realisation_moyen_mois}
            }
        ))

        # Mettre à jour le fond en noir pour les jauges mensuelles
        fig_suivi_mois.update_layout(paper_bgcolor="black", plot_bgcolor="black", font={'color': "white"})
        fig_completion_mois.update_layout(paper_bgcolor="black", plot_bgcolor="black", font={'color': "white"})

        # Afficher les jauges mensuelles côte à côte
        col1, col2 = st.columns(2)
        with col1:
            st.subheader('Taux de Suivi Mensuel')
            st.plotly_chart(fig_suivi_mois)
        with col2:
            st.subheader('Taux de Réalisation Mensuel')
            st.plotly_chart(fig_completion_mois)

        st.subheader("Comparatif des taux de suivi par mois")
        # Graphique : Taux de suivi des parcours par mois
        all_months_taux_suivi = []
        for month in range(1, 13):
            monthly_data = details_df[details_df['mois'] == month]
            semaines_du_mois = monthly_data['semaine'].unique()
            weekly_taux_suivi = []
            for semaine in semaines_du_mois:
                weekly_comparison_table = create_parcours_comparison_table(semaine, details_df, planning_df)
                taux_suivi_semaine = calculate_taux_suivi_from_table(weekly_comparison_table)
                weekly_taux_suivi.append(taux_suivi_semaine)
            taux_suivi_moyen_mois = sum(weekly_taux_suivi) / len(weekly_taux_suivi) if weekly_taux_suivi else 0
            all_months_taux_suivi.append(taux_suivi_moyen_mois)

        fig_taux_suivi = px.bar(x=list(mois_dict.values()), y=all_months_taux_suivi,
                                title='Taux de suivi des parcours par mois',
                                labels={'x': 'Mois', 'y': 'Taux de suivi (%)'},
                                template='plotly_dark')
        fig_taux_suivi.update_layout(xaxis_tickangle=-45, xaxis_title="", yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig_taux_suivi)
        st.subheader("Taux de réalisation par parcours")
        # Graphique : Taux de réalisation par parcours
        monthly_data = details_df1[details_df1['mois'] == selected_month]
        completion_rates, _ = calculate_completion_rates(monthly_data)  # Déballage du tuple
        completion_rates_df = completion_rates.reset_index()
        completion_rates_df.columns = ['cleaning_plan', 'task_completion_(%)']

        fig_hist = px.bar(completion_rates_df, x='cleaning_plan', y='task_completion_(%)',
                          title=f'Taux de réalisation par parcours (Mois de {mois_dict[selected_month]})',
                          labels={'cleaning_plan': 'Parcours', 'task_completion_(%)': 'Taux de réalisation (%)'},
                          template='plotly_dark')
        fig_hist.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="Seuil de réalisation (90%)")
        fig_hist.update_layout(xaxis_tickangle=-45, xaxis_title="", yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig_hist)

        st.subheader("Comparatif des taux de réalisation par mois")
        # Graphique : Comparatif des taux de réalisation par mois
        all_months_completion_rates = []
        for month in range(1, 13):
            monthly_data = details_df[details_df['mois'] == month]
            _, taux_realisation = calculate_completion_rates(monthly_data)
            all_months_completion_rates.append(taux_realisation)
        
        comparative_df = pd.DataFrame({
            'Mois': list(mois_dict.values()),
            'Taux de réalisation': all_months_completion_rates
        })
        
        fig_comparative = px.bar(comparative_df, x='Mois', y='Taux de réalisation',
                                 title='Comparatif des taux de réalisation des parcours par mois',
                                 labels={'Taux de réalisation': 'Taux de réalisation (%)'},
                                 template='plotly_dark')
        fig_comparative.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="Seuil de réalisation (90%)")
        fig_comparative.update_layout(xaxis_title="", yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig_comparative)

    if 'current_app' not in st.session_state:
        st.session_state.current_app = "ECOBOT 40"
    st.subheader("Actions correctives")

    # Fonction pour charger les actions correctives depuis un fichier Excel
    def load_actions_correctives():
        try:
            df = pd.read_excel('actions_correctives_ECOBOT40.xlsx', parse_dates=['Date d\'ajout', 'Délai d\'intervention'])
            df['Date d\'ajout'] = pd.to_datetime(df['Date d\'ajout']).dt.date
            df['Délai d\'intervention'] = pd.to_datetime(df['Délai d\'intervention']).dt.date
            return df
        except FileNotFoundError:
            return pd.DataFrame(columns=['Action corrective', 'Date d\'ajout', 'Délai d\'intervention', 'Responsable Action', 'Statut', 'Commentaires'])

    # Fonction pour sauvegarder les actions correctives dans un fichier Excel
    def save_actions_correctives(df):
        df['Date d\'ajout'] = pd.to_datetime(df['Date d\'ajout'])
        df['Délai d\'intervention'] = pd.to_datetime(df['Délai d\'intervention'])
        df.to_excel('actions_correctives_ECOBOT40.xlsx', index=False)

    # Initialiser le state si nécessaire
    if 'actions_correctives_ECOBOT40' not in st.session_state:
        st.session_state.actions_correctives_ECOBOT40 = load_actions_correctives()

    if 'editing_ECOBOT40' not in st.session_state:
        st.session_state.editing_ECOBOT40 = False

    # S'assurer qu'il y a toujours au moins une ligne dans le DataFrame
    if len(st.session_state.actions_correctives_ECOBOT40) == 0:
        st.session_state.actions_correctives_ECOBOT40 = pd.DataFrame({
            'Action corrective': ['Action 1 pour ECOBOT 40'],
            'Date d\'ajout': [datetime.now().date()],
            'Délai d\'intervention': [(datetime.now() + timedelta(days=7)).date()],
            'Responsable Action': ['Responsable 1'],
            'Statut': ['En cours'],
            'Commentaires': ['Commentaires à faire']
        })

    # Fonction pour basculer le mode d'édition
    def toggle_edit_mode_ECOBOT40():
        st.session_state.editing_ECOBOT40 = not st.session_state.editing_ECOBOT40

    # Bouton pour basculer entre le mode d'édition et de visualisation
    st.button("Modifier les actions correctives" if not st.session_state.editing_ECOBOT40 else "Terminer l'édition", 
              on_click=toggle_edit_mode_ECOBOT40, key='toggle_edit_ECOBOT40')

    if st.session_state.editing_ECOBOT40:
        # Mode d'édition
        edited_df = st.data_editor(
            st.session_state.actions_correctives_ECOBOT40,
            num_rows="dynamic",
            column_config={
                "Action corrective": st.column_config.TextColumn(
                    "Action corrective",
                    help="Décrivez l'action corrective",
                    max_chars=100,
                    width="large",
                ),
                "Date d'ajout": st.column_config.DateColumn(
                    "Date d'ajout",
                    help="Date d'ajout de l'action",
                    format="DD/MM/YYYY",
                    width="medium",
                ),
                "Délai d'intervention": st.column_config.DateColumn(
                    "Délai d'intervention",
                    help="Date limite pour l'action",
                    format="DD/MM/YYYY",
                    width="medium",
                ),
                "Responsable Action": st.column_config.TextColumn(
                    "Responsable Action",
                    help="Personne responsable de l'action",
                    max_chars=50,
                    width="medium",
                ),
                "Statut": st.column_config.SelectboxColumn(
                    "Statut",
                    help="Statut actuel de l'action",
                    options=['En cours', 'Terminé', 'En retard'],
                    width="small",
                ),
                "Commentaires": st.column_config.TextColumn(
                    "Commentaires",
                    help="Commentaires additionnels",
                    max_chars=200,
                    width="large",
                ),
            },
            hide_index=True,
            width=2000,
            key='data_editor_ECOBOT40'
        )

        if st.button("Sauvegarder les modifications", key='save_ECOBOT40'):
            st.session_state.actions_correctives_ECOBOT40 = edited_df
            save_actions_correctives(edited_df)
            st.success("Les actions correctives pour ECOBOT 40 ont été mises à jour et sauvegardées.")
            st.session_state.editing_ECOBOT40 = False
    else:
        # Mode de visualisation
        st.dataframe(st.session_state.actions_correctives_ECOBOT40, width=2000)

    # Bouton pour télécharger le fichier Excel
    if st.button("Télécharger le fichier Excel", key='download_ECOBOT40'):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.actions_correctives_ECOBOT40.to_excel(writer, index=False)
        output.seek(0)
        st.download_button(
            label="Cliquez ici pour télécharger",
            data=output,
            file_name="actions_correctives_ECOBOT40.xlsx",
            key="download_button_ECOBOT40",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
if __name__ == '__main__':
    main()
