import folium

def construire_carte(points, ordre, geometrie=None):
    depot = points[0]
    carte = folium.Map(location=[depot["lat"], depot["lon"]], zoom_start=13,
                       control_scale=True)
    for rang, idx in enumerate(ordre):
        p = points[idx]
        if idx == 0:
            folium.Marker([p["lat"],p["lon"]], tooltip="Entrepôt — départ/arrivée",
                icon=folium.Icon(color="red", icon="star")).add_to(carte)
        else:
            html = (f'<div style="font-size:11px;font-weight:bold;color:white;'
                    f'background:#1769aa;border:1px solid white;border-radius:50%;'
                    f'width:22px;height:22px;text-align:center;line-height:22px;">{rang}</div>')
            folium.Marker([p["lat"],p["lon"]],
                tooltip=f'Visite {rang} — {p["nom"]} ({p["quartier"]})',
                icon=folium.DivIcon(html=html)).add_to(carte)
    if geometrie:
        folium.PolyLine(geometrie, color="blue", weight=5,
                        tooltip="Itinéraire routier OSRM").add_to(carte)
    else:
        ligne = [[points[i]["lat"],points[i]["lon"]] for i in ordre]
        ligne.append([depot["lat"],depot["lon"]])
        folium.PolyLine(ligne, color="orange", weight=3, dash_array="6, 8",
                        tooltip="Liaison estimée — OSRM indisponible").add_to(carte)
    folium.LayerControl().add_to(carte)
    return carte

def creer_carte(points, ordre, chemin="tsp_fes_resultat.html", geometrie=None):
    carte = construire_carte(points, ordre, geometrie)
    carte.save(chemin)
    return chemin
