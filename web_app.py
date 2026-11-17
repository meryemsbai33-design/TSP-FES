import csv
import io

import streamlit as st
from streamlit_folium import st_folium

from tsp_fes.agents import agent_raisonneur, agent_scholar, agent_web
from tsp_fes.carte import construire_carte
from tsp_fes.donnees import construire_points
from tsp_fes.genetique import algorithme_genetique
from tsp_fes.optuna_optimizer import optimiser_avec_optuna
from tsp_fes.osrm import (
    matrice_estimee,
    obtenir_matrice_osrm,
    obtenir_route_osrm,
)

st.set_page_config(page_title="TSP FES", page_icon="🗺️", layout="wide")
st.title("TSP FES — Optimisation d’un circuit à Fès")
st.caption("40 points · neuf quartiers · départ et retour à l’entrepôt d’Agdal")

points = construire_points()
if "matrice" not in st.session_state:
    st.session_state.matrice = None
    st.session_state.mode_distance = None
if "resultat" not in st.session_state:
    st.session_state.resultat = None

with st.sidebar:
    st.header("Configuration")
    mode = st.selectbox("Mode de calcul", ["Manuel", "Optuna", "Agents IA"])
    if mode == "Manuel":
        taille_population = st.select_slider(
            "Taille de population", options=[50, 100, 500], value=100
        )
        selection = st.selectbox("Sélection", ["Tournoi", "RO"])
        taux_mutation = st.select_slider(
            "Taux de mutation", options=[0.2, 0.5, 0.8], value=0.2
        )
        taux_croisement = st.select_slider(
            "Taux de croisement", options=[0.2, 0.5, 0.8], value=0.8
        )
        generations = st.select_slider(
            "Générations", options=[100, 500, 1000], value=500
        )
    else:
        st.info(
            "Optuna sélectionne les paramètres automatiquement."
            if mode == "Optuna"
            else "Les agents consultent le Web et OpenAlex pour proposer des paramètres."
        )
    lancer = st.button("Calculer le circuit", type="primary", use_container_width=True)

if lancer:
    progression = st.progress(0, text="Préparation des distances…")
    try:
        if st.session_state.matrice is None:
            try:
                st.session_state.matrice = obtenir_matrice_osrm(points)
                st.session_state.mode_distance = "Distances routières OSRM"
            except Exception as exc:
                st.session_state.matrice = matrice_estimee(points)
                st.session_state.mode_distance = "Estimation géographique"
                st.warning(
                    f"OSRM est indisponible ({exc}). "
                    "Les distances affichées seront des estimations, pas des distances routières."
                )

        matrice = st.session_state.matrice
        if mode == "Optuna":
            progression.progress(10, text="Optuna optimise les paramètres…")
            params, score_calibration = optimiser_avec_optuna(matrice, n_trials=15)
            st.info(
                f"Paramètres Optuna : {params} · "
                f"score de calibration : {score_calibration:.2f} km"
            )
        elif mode == "Agents IA":
            progression.progress(10, text="Recherche Web et scientifique…")
            web = agent_web()
            scholar = agent_scholar()
            params, explication = agent_raisonneur(web, scholar)
            st.info(f"{explication} Paramètres proposés : {params}")
            st.caption(
                f"Sources : {web['source']} et {scholar['source']}. "
                "Les recommandations sont indicatives."
            )
        else:
            params = {
                "taille_population": taille_population,
                "selection": selection,
                "taux_mutation": taux_mutation,
                "taux_croisement": taux_croisement,
                "generations": generations,
            }

        progression.progress(20, text="Calcul du circuit génétique…")

        def suivre_progression(generation, total):
            progression.progress(
                20 + int(80 * generation / total),
                text=f"Génération {generation}/{total}",
            )

        ordre, score, historique = algorithme_genetique(
            matrice,
            params["taille_population"],
            params["selection"],
            params["taux_mutation"],
            params["taux_croisement"],
            params["generations"],
            callback=suivre_progression,
        )

        geometrie = None
        distance_route = None
        if st.session_state.mode_distance == "Distances routières OSRM":
            try:
                geometrie, distance_route = obtenir_route_osrm(points, ordre)
            except Exception as exc:
                st.warning(f"Géométrie OSRM indisponible : {exc}")

        st.session_state.resultat = {
            "ordre": ordre,
            "score": score,
            "historique": historique,
            "geometrie": geometrie,
            "distance_route": distance_route,
            "params": params,
        }
        progression.empty()
    except Exception as exc:
        progression.empty()
        st.error(f"Le calcul a échoué : {exc}")

resultat = st.session_state.resultat
if resultat:
    ordre = resultat["ordre"]
    distance = resultat["distance_route"] or resultat["score"]
    mode_distance = st.session_state.mode_distance

    col_distance, col_points, col_mode = st.columns(3)
    col_distance.metric("Distance du circuit", f"{distance:.2f} km")
    col_points.metric("Points visités", str(len(ordre)))
    col_mode.metric("Source des distances", mode_distance)

    st.subheader("Itinéraire")
    carte = construire_carte(points, ordre, resultat["geometrie"])
    st_folium(carte, height=560, use_container_width=True, returned_objects=[])

    st.download_button(
        "Télécharger la carte HTML",
        data=carte.get_root().render(),
        file_name="tsp_fes_resultat.html",
        mime="text/html",
    )

    gauche, droite = st.columns(2)
    with gauche:
        st.subheader("Convergence")
        st.line_chart({"Meilleure distance (km)": resultat["historique"]})
    with droite:
        st.subheader("Ordre de visite")
        lignes = [
            {
                "Ordre": rang,
                "Point": points[index]["nom"],
                "Quartier": points[index]["quartier"],
            }
            for rang, index in enumerate(ordre)
        ]
        st.dataframe(lignes, width="stretch", hide_index=True)

    sortie_csv = io.StringIO()
    writer = csv.DictWriter(sortie_csv, fieldnames=["Ordre", "Point", "Quartier"])
    writer.writeheader()
    writer.writerows(lignes)
    st.download_button(
        "Télécharger l’ordre de visite CSV",
        data=sortie_csv.getvalue(),
        file_name="tsp_fes_itineraire.csv",
        mime="text/csv",
    )
else:
    st.info("Choisis un mode dans le panneau latéral, puis lance le calcul.")

st.caption(
    "Les coordonnées sont des points de démonstration. "
    "OSRM et les tuiles de carte nécessitent une connexion Internet."
)
