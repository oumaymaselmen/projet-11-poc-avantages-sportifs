import os
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(
    f"postgresql+pg8000://sds_admin:{os.getenv('POSTGRES_PASSWORD')}@sds_postgres:5432/avantages_sportifs"
)

ORS_API_KEY = os.getenv("ORS_API_KEY")
ADRESSE_BUREAU = "1362 Avenue des Platanes, 34970 Lattes, France"

DISTANCE_MAX = {
    "Marche/running": 15,
    "Vélo/Trottinette/Autres": 25,
}

def geocoder_adresse(adresse):
    url = "https://api.openrouteservice.org/geocode/search"
    params = {"api_key": ORS_API_KEY, "text": adresse, "size": 1}
    response = requests.get(url, params=params)
    data = response.json()
    if data["features"]:
        coords = data["features"][0]["geometry"]["coordinates"]
        return coords[0], coords[1]
    return None, None

def calculer_distance(lon1, lat1, lon2, lat2, mode):
    profile_map = {
        "Marche/running": "foot-walking",
        "Vélo/Trottinette/Autres": "cycling-regular",
    }
    profile = profile_map.get(mode, "foot-walking")
    url = f"https://api.openrouteservice.org/v2/directions/{profile}"
    headers = {"Authorization": ORS_API_KEY}
    body = {"coordinates": [[lon1, lat1], [lon2, lat2]]}
    response = requests.post(url, json=body, headers=headers)
    data = response.json()
    if "routes" in data:
        distance_m = data["routes"][0]["summary"]["distance"]
        return round(distance_m / 1000, 2)
    return None

print("=== VALIDATION DISTANCES DOMICILE/BUREAU ===\n")

lon_bureau, lat_bureau = geocoder_adresse(ADRESSE_BUREAU)
print(f"Bureau geocode : lon={lon_bureau}, lat={lat_bureau}")

with engine.begin() as conn:
    # Uniquement les salaries pas encore verifies
    employes = conn.execute(text("""
        SELECT id_salarie, nom, prenom, adresse_domicile, moyen_deplacement
        FROM employes
        WHERE moyen_deplacement IN ('Marche/running', 'Vélo/Trottinette/Autres')
        AND id_salarie NOT IN (SELECT id_salarie FROM distances_domicile_bureau)
    """)).fetchall()

    print(f"{len(employes)} nouveaux salaries a valider\n")

    nb_valide = 0
    nb_invalide = 0

    for emp in employes:
        id_salarie, nom, prenom, adresse, mode = emp

        lon_dom, lat_dom = geocoder_adresse(adresse)
        if lon_dom is None:
            print(f"Adresse non trouvee : {prenom} {nom}")
            continue

        distance_km = calculer_distance(lon_dom, lat_dom, lon_bureau, lat_bureau, mode)
        if distance_km is None:
            print(f"Distance non calculable : {prenom} {nom}")
            continue

        distance_max = DISTANCE_MAX.get(mode, 15)
        valide = distance_km <= distance_max
        motif = None if valide else f"{distance_km}km > {distance_max}km max pour {mode}"

        if valide:
            nb_valide += 1
        else:
            nb_invalide += 1

        conn.execute(text("""
            INSERT INTO distances_domicile_bureau
                (id_salarie, adresse_domicile, distance_km, mode_transport_declare,
                 distance_max_km, declaration_valide, motif_invalide)
            VALUES (:id_salarie, :adresse, :distance_km, :mode, :distance_max, :valide, :motif)
            ON CONFLICT (id_salarie) DO UPDATE SET
                distance_km = EXCLUDED.distance_km,
                declaration_valide = EXCLUDED.declaration_valide,
                motif_invalide = EXCLUDED.motif_invalide,
                date_verification = NOW()
        """), {
            "id_salarie": id_salarie,
            "adresse": adresse,
            "distance_km": distance_km,
            "mode": mode,
            "distance_max": distance_max,
            "valide": valide,
            "motif": motif
        })

print(f"\n=== RESUME ===")
print(f"Declarations valides : {nb_valide}")
print(f"Declarations invalides : {nb_invalide}")
print("Termine !")