import math
import requests

TABLE_URL = "https://router.project-osrm.org/table/v1/driving/"
ROUTE_URL = "https://router.project-osrm.org/route/v1/driving/"

def haversine_km(a, b):
    """Distance à vol d'oiseau en kilomètres."""
    r = 6371.0088
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp = p2 - p1
    dl = math.radians(b["lon"] - a["lon"])
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(math.sqrt(h))

def matrice_estimee(points, facteur_detour=1.28):
    """Approximation en l'absence d'OSRM."""
    return [[0.0 if i == j else haversine_km(points[i], points[j])*facteur_detour
             for j in range(len(points))] for i in range(len(points))]

def obtenir_matrice_osrm(points, timeout=40):
    coords = ";".join(f'{p["lon"]},{p["lat"]}' for p in points)
    r = requests.get(TABLE_URL + coords, params={"annotations": "distance"}, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if data.get("code") != "Ok" or not data.get("distances"):
        raise RuntimeError(f"Réponse OSRM invalide : {data.get('code')}")
    # Si OSRM ne trouve pas un trajet entre deux points (valeur null),
    # on déclenche le fallback global plutôt que d'injecter des coûts infinis.
    if any(x is None for row in data["distances"] for x in row):
        raise RuntimeError("OSRM n'a pas trouvé de liaison routière pour certaines paires de points.")
    return [[float(x)/1000 for x in row] for row in data["distances"]]

def obtenir_route_osrm(points, ordre, timeout=50):
    sequence = list(ordre) + [ordre[0]]
    coords = ";".join(f'{points[i]["lon"]},{points[i]["lat"]}' for i in sequence)
    r = requests.get(ROUTE_URL + coords,
        params={"overview": "full", "geometries": "geojson", "steps": "false"},
        timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise RuntimeError(f"Itinéraire OSRM invalide : {data.get('code')}")
    route = data["routes"][0]
    latlon = [[lat, lon] for lon, lat in route["geometry"]["coordinates"]]
    return latlon, route["distance"]/1000
