import re
import requests

def agent_web():
    """Recherche de bonnes pratiques via DuckDuckGo HTML."""
    fallback = {"taille_population":100, "selection":"Tournoi",
                "taux_mutation":.2, "taux_croisement":.8, "generations":500}
    try:
        r = requests.get("https://html.duckduckgo.com/html/",
            params={"q":"genetic algorithm TSP order crossover tournament mutation rate"},
            headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        r.raise_for_status()
        texte = re.sub(r"\\s+", " ", re.sub(r"<[^>]+>", " ", r.text))[:1600]
        return {"source":"DuckDuckGo", "texte":texte, "proposition":fallback}
    except Exception as e:
        return {"source":"Web indisponible", "texte":str(e), "proposition":fallback}

def agent_scholar():
    """Recherche d'articles scientifiques avec l'API OpenAlex."""
    fallback = {"taille_population":100, "selection":"RO",
                "taux_mutation":.5, "taux_croisement":.8, "generations":500}
    try:
        r = requests.get("https://api.openalex.org/works",
            params={"search":"genetic algorithm traveling salesman problem TSP",
                    "per-page":5, "sort":"relevance_score:desc"}, timeout=20)
        r.raise_for_status()
        works = r.json().get("results", [])
        articles = [{"titre":w.get("title"), "annee":w.get("publication_year"),
                     "doi":w.get("doi")} for w in works]
        return {"source":"OpenAlex", "articles":articles, "proposition":fallback}
    except Exception as e:
        return {"source":"Scholar indisponible", "articles":[], "erreur":str(e),
                "proposition":fallback}

def agent_raisonneur(web, scholar):
    """Arbitrage déterministe des propositions Web et Scholar."""
    w, s = web["proposition"], scholar["proposition"]
    params = {}
    for key in w:
        if w[key] == s[key]:
            params[key] = w[key]
        elif key == "taille_population":
            params[key] = 100
        elif key == "selection":
            params[key] = "Tournoi"
        elif key == "taux_mutation":
            params[key] = .2
        elif key == "taux_croisement":
            params[key] = .8
        else:
            params[key] = 500
    explication = ("Compromis heuristique : population intermédiaire, tournoi, "
                   "croisement élevé et mutation modérée. Les agents donnent une "
                   "recommandation indicative, pas une garantie d'optimum.")
    return params, explication
