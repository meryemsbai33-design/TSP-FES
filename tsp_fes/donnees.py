# Centres approximatifs des neuf quartiers (latitude, longitude).
QUARTIERS = {
    "Fès el-Bali": (34.0648, -4.9770),
    "Fès el-Jdid": (34.0524, -4.9990),
    "Ville Nouvelle": (34.0395, -5.0030),
    "Agdal": (34.0340, -4.9990),
    "Narjiss": (34.0585, -5.0120),
    "Atlas": (34.0270, -5.0000),
    "Zouagha": (34.0050, -5.0120),
    "Bensouda": (34.0020, -5.0350),
    "Route d'Immouzer": (34.0180, -4.9870),
}
DEPOT = {"id": 0, "nom": "Entrepôt — Agdal", "quartier": "Agdal",
         "lat": 34.0330, "lon": -4.9960, "depot": True}

# Répartition totale : 39 points visiteurs + le dépôt = 40 points.
# Les trois premiers quartiers ont 5 points ; les six autres en ont 4.
OFFSETS = [(-.0020, -.0020), (-.0010, .0015), (.0012, -.0010),
           (.0020, .0020), (0.0, .0030)]

def construire_points():
    points = [DEPOT.copy()]
    for k, (nom, centre) in enumerate(QUARTIERS.items()):
        for j in range(5 if k < 3 else 4):
            dlat, dlon = OFFSETS[j]
            points.append({
                "id": len(points), "nom": f"Point {len(points):02d}",
                "quartier": nom,
                "lat": centre[0] + dlat + (k % 2) * .00035,
                "lon": centre[1] + dlon - (k % 3) * .00025,
                "depot": False
            })
    assert len(points) == 40
    return points
