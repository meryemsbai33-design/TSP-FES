"""Interface web Streamlit du projet TSP FES."""
import math
import streamlit as st
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

from tsp_fes.donnees import construire_points
from tsp_fes.osrm import obtenir_matrice_osrm, matrice_estimee, obtenir_route_osrm
from tsp_fes.genetique import algorithme_genetique
from tsp_fes.optuna_optimizer import optimiser_avec_optuna
from tsp_fes.agents import agent_web, agent_scholar, agent_raisonneur

st.set_page_config(page_title="TSP FES", page_icon="📍", layout="wide")

st.title("📍 TSP FES — Optimisation de tournée à Fès")
st.caption("Problème du voyageur de commerce • 40 points • Algorithme génétique • OSRM")

points = construire_points()

# Initialisation des résultats conservés entre les interactions Streamlit.
if "resultat_tsp" not in st.session_state:
    st.session_state.resultat_tsp = None
if "matrice_tsp" not in st.session_state:
    st.session_state.matrice_tsp = None
if "mode_distances" not in st.session_state:
    st.session_state.mode_distances = None

with st.sidebar:
    st.header("1. Définition et paramètres")
    st.info("Ville : Fès\n\nNombre de points : 40\n\nDépôt : Agdal")
    taille = st.selectbox("Topsize (population)", [50, 100, 500], index=1)
    selection = st.selectbox("Méthode de sélection", ["RO", "Tournoi"], index=1)
    mutation = st.selectbox("Taux de mutation", [0.2, 0.5, 0.8], index=0)
    croisement = st.selectbox("Taux de croisement", [0.2, 0.5, 0.8], index=2)
    generations = st.selectbox("Nombre de générations", [100, 500, 1000], index=1)
    st.divider()
    mode = st.radio("Mode de réglage", ["B1 — Manuel", "B2 — Optuna", "B3 — IA agentique"])
    lancer = st.button("🚀 Lancer l'optimisation", type="primary", use_container_width=True)

st.subheader("2. Résultats")
progress_bar = st.progress(0, text="En attente du lancement…")
status = st.empty()

if lancer:
    params = {
        "taille_population": taille,
        "selection": selection,
        "taux_mutation": mutation,
        "taux_croisement": croisement,
        "generations": generations,
    }

    try:
        # B2 : optimisation des hyperparamètres par Optuna.
        if mode.startswith("B2"):
            status.info("Optuna recherche une bonne configuration (15 essais)…")
            if st.session_state.matrice_tsp is None:
                try:
                    st.session_state.matrice_tsp = obtenir_matrice_osrm(points)
                    st.session_state.mode_distances = "Distances routières OSRM"
                except Exception as exc:
                    st.warning(f"OSRM indisponible : {exc}. Utilisation d'une estimation.")
                    st.session_state.matrice_tsp = matrice_estimee(points)
                    st.session_state.mode_distances = "Estimation géographique"
            params, score_optuna = optimiser_avec_optuna(st.session_state.matrice_tsp, n_trials=15)
            st.success(f"Optuna terminé. Meilleurs paramètres : {params} (score d'essai : {score_optuna:.2f} km)")

        # B3 : agents Web, Scholar et raisonneur.
        elif mode.startswith("B3"):
            status.info("Agent Web : recherche de bonnes pratiques…")
            resultat_web = agent_web()
            with st.expander("Proposition de l'agent Web", expanded=False):
                st.write(resultat_web)
            progress_bar.progress(15, text="Agent Web terminé")

            status.info("Agent Scholar : recherche d'articles scientifiques…")
            resultat_scholar = agent_scholar()
            with st.expander("Résultats de l'agent Scholar", expanded=False):
                st.write(resultat_scholar)
            progress_bar.progress(35, text="Agent Scholar terminé")

            params, justification = agent_raisonneur(resultat_web, resultat_scholar)
            st.info(f"Arbitrage du raisonneur : {justification}")
            st.write("Paramètres retenus :", params)

        # Construire la matrice OSRM une seule fois, puis la conserver en session.
        if st.session_state.matrice_tsp is None:
            status.info("Calcul de la matrice des distances entre les 40 points…")
            try:
                st.session_state.matrice_tsp = obtenir_matrice_osrm(points)
                st.session_state.mode_distances = "Distances routières OSRM"
            except Exception as exc:
                st.warning(
                    f"Le service OSRM n'est pas disponible ({exc}). "
                    "Le calcul continue avec une estimation géographique, qui n'est pas un routage réel."
                )
                st.session_state.matrice_tsp = matrice_estimee(points)
                st.session_state.mode_distances = "Estimation géographique (OSRM indisponible)"

        matrice = st.session_state.matrice_tsp
        n_gen = int(params["generations"])
        progress_bar.progress(0, text="Algorithme génétique en cours…")
        status.info(f"Exécution du GA : population {params['taille_population']}, {n_gen} générations.")

        def maj_progression(generation, total):
            # Le callback est appelé à chaque génération par l'algorithme génétique.
            fraction = min(generation / total, 1.0)
            progress_bar.progress(fraction, text=f"Génération {generation}/{total} — {fraction:.0%}")

        ordre, distance, historique = algorithme_genetique(
            matrice,
            taille_population=int(params["taille_population"]),
            selection=params["selection"],
            taux_mutation=float(params["taux_mutation"]),
            taux_croisement=float(params["taux_croisement"]),
            generations=n_gen,
            callback=maj_progression,
        )

        geometrie = None
        distance_osrm = None
        if st.session_state.mode_distances == "Distances routières OSRM":
            try:
                geometrie, distance_osrm = obtenir_route_osrm(points, ordre)
            except Exception as exc:
                st.warning(f"Le tracé détaillé OSRM n'a pas pu être récupéré : {exc}")

        st.session_state.resultat_tsp = {
            "ordre": ordre,
            "distance": distance,
            "historique": historique,
            "geometrie": geometrie,
            "distance_osrm": distance_osrm,
            "params": params,
        }
        progress_bar.progress(1.0, text="Optimisation terminée.")
        status.success("Calcul terminé avec succès.")

    except Exception as exc:
        status.error(f"Erreur pendant l'optimisation : {exc}")

resultat = st.session_state.resultat_tsp

if resultat is None:
    st.info("Choisis les paramètres dans le panneau de gauche, puis clique sur « Lancer l'optimisation ».")
else:
    ordre = resultat["ordre"]
    historique = resultat["historique"]
    distance_affichee = resultat["distance_osrm"] or resultat["distance"]

    c1, c2 = st.columns([1, 1])
    with c1:
        st.metric("Distance totale du circuit", f"{distance_affichee:.2f} km")
        st.caption(st.session_state.mode_distances)
    with c2:
        st.metric("Nombre de points visités", "40")
        st.caption("Départ et arrivée à l'entrepôt d'Agdal")

    st.markdown("#### Courbe de convergence")
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.plot(range(1, len(historique) + 1), historique)
    ax.set_xlabel("Génération")
    ax.set_ylabel("Meilleure distance (km)")
    ax.grid(True, alpha=0.25)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.markdown("#### Chromosome solution")
    noms = [points[i]["nom"] for i in ordre]
    st.code(" → ".join(noms) + " → Entrepôt", language="text")

    # Quadrant 3 : plan cartésien local (projection approximative en kilomètres).
    st.subheader("3. Plan cartésien du TSP")
    lat0 = sum(p["lat"] for p in points) / len(points)
    lon0 = sum(p["lon"] for p in points) / len(points)
    xy = [
        ((p["lon"] - lon0) * 111.32 * math.cos(math.radians(lat0)),
         (p["lat"] - lat0) * 110.574)
        for p in points
    ]
    fig2, ax2 = plt.subplots(figsize=(9, 5))
    for p, (x, y) in zip(points, xy):
        if p["depot"]:
            ax2.scatter(x, y, marker="*", s=250, color="red", label="Entrepôt", zorder=5)
            ax2.annotate("Dépôt", (x, y), xytext=(5, 7), textcoords="offset points")
        else:
            ax2.scatter(x, y, s=25, color="steelblue")
            ax2.annotate(str(p["id"]), (x, y), xytext=(3, 3), textcoords="offset points", fontsize=7)
    trajet = [xy[i] for i in ordre] + [xy[ordre[0]]]
    ax2.plot([v[0] for v in trajet], [v[1] for v in trajet], color="darkorange", linewidth=1.3)
    ax2.set_xlabel("Est-Ouest (km)")
    ax2.set_ylabel("Nord-Sud (km)")
    ax2.grid(True, alpha=0.25)
    ax2.legend()
    st.pyplot(fig2, use_container_width=True)
    plt.close(fig2)

    # Quadrant 4 : carte interactive Folium.
    st.subheader("4. Routage réel cartographié — Fès")
    depot = points[0]
    carte = folium.Map(location=[depot["lat"], depot["lon"]], zoom_start=13, control_scale=True)
    for rang, idx in enumerate(ordre):
        p = points[idx]
        if idx == 0:
            folium.Marker(
                [p["lat"], p["lon"]],
                tooltip="Entrepôt — départ et arrivée",
                icon=folium.Icon(color="red", icon="home"),
            ).add_to(carte)
        else:
            folium.Marker(
                [p["lat"], p["lon"]],
                tooltip=f"Visite {rang} — {p['nom']} ({p['quartier']})",
                icon=folium.DivIcon(html=(
                    f'<div style="background:#1769aa;color:white;border:1px solid white;'
                    f'border-radius:50%;width:24px;height:24px;text-align:center;'
                    f'line-height:24px;font-weight:bold">{rang}</div>'
                )),
            ).add_to(carte)

    if resultat["geometrie"]:
        folium.PolyLine(resultat["geometrie"], color="blue", weight=5, tooltip="Itinéraire routier OSRM").add_to(carte)
    else:
        ligne = [[points[i]["lat"], points[i]["lon"]] for i in ordre]
        ligne.append([depot["lat"], depot["lon"]])
        folium.PolyLine(
            ligne, color="orange", weight=3, dash_array="6, 8",
            tooltip="Liaison estimée — OSRM indisponible",
        ).add_to(carte)

    st_folium(carte, use_container_width=True, height=600, returned_objects=[])
    if not resultat["geometrie"]:
        st.warning("La carte affiche des liaisons approximatives : le tracé routier OSRM n'a pas été obtenu.")
