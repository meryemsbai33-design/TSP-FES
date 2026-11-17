# TSP FES — Optimisation d’un circuit à Fès

Projet de démonstration du problème du voyageur de commerce avec 40 points,
répartis dans neuf quartiers de Fès et un entrepôt de départ/retour à Agdal.

## Application Web (Streamlit + Folium)

### Lancer localement

Dans le dossier du projet :

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run web_app.py
```

Le navigateur s’ouvrira sur `http://localhost:8501`. L’application propose le
mode manuel, l’optimisation Optuna, les recommandations des agents, une carte
Folium interactive et le téléchargement de la carte et de l’ordre de visite.

### Déployer gratuitement avec Streamlit Community Cloud

1. Crée un dépôt GitHub et téléverse les fichiers du projet, en excluant `.venv`.
2. Connecte-toi à [share.streamlit.io](https://share.streamlit.io/) avec GitHub.
3. Choisis **Create app**, le dépôt et la branche.
4. Indique `web_app.py` comme fichier principal, puis déploie.
5. Streamlit installe les bibliothèques depuis `requirements.txt`.

Le déploiement public requiert un compte GitHub et un dépôt accessible au service.
Les coordonnées de démonstration ne contiennent pas de données personnelles.

## Application de bureau Tkinter

L’interface Tkinter d’origine reste disponible :

```powershell
python main.py
```

Elle enregistre la carte Folium localement et l’ouvre dans le navigateur.

## Modes et limites

- **Manuel** : lance l’algorithme génétique avec les paramètres choisis.
- **Optuna** : essaie 15 configurations puis exécute le meilleur paramétrage.
- **Agents IA** : interroge DuckDuckGo et OpenAlex, puis arbitre avec des règles
  heuristiques ; il ne s’agit pas d’un LLM autonome.
- Le routage et les tuiles cartographiques nécessitent Internet. Si OSRM ne
  répond pas, l’application signale et utilise une estimation géographique,
  qui n’est pas une distance routière.
- Les 40 coordonnées sont des points de démonstration, pas des adresses
  commerciales vérifiées. Le GA est heuristique et ne garantit pas l’optimum.
- Le service OSRM public peut imposer des limites et ne convient pas à un usage
  de production.
