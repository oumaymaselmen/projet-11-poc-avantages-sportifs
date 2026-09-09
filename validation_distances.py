import requests
from sqlalchemy import create_engine, text
import os
import time
import math
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5435')

engine = create_engine(
    f"postgresql+pg8000://sds_admin:{os.getenv('POSTGRES_PASSWORD')}@{DB_HOST}:{DB_PORT}/avantages_sportifs"
)

ADRESSE_BUREAU = "1362 Avenue des Platanes, 34970 Lattes, France"
COEF_ROUTIER = 1.3

DISTANCE_MAX = {
    "Marche/running": 15,
    "Vélo/Trottinette/Autres": 25,
}

def geocoder_adresse(adresse):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": adresse, "format": "json", "limit": 1}
    headers = {"User-Agent": "SportDataSolution-POC/1.0"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        if data:
            return float(data[0]["lon"]), float(data[0]["lat"])
    except Exception as e:
        print(f"Erreur geocodage : {e}")
    return None, None

def haversine(lon1, lat1, lon2, lat2):
    R = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

print("=== VALIDATION DISTANCES DOMICILE/BUREAU ===\n")

with engine.begin() as conn:
    employes = conn.execute(text("""
        SELECT id_salarie, nom, prenom, adresse_domicile, moyen_deplacement
        FROM employes
        WHERE moyen_deplacement IN ('Marche/running', 'Vélo/Trottinette/Autres')
        AND id_salarie NOT IN (SELECT id_salarie FROM distances_domicile_bureau)
    """)).fetchall()

    print(f"{len(employes)} nouveaux salaries a valider\n")

    if len(employes) == 0:
        print("Toutes les distances sont deja validees - aucun appel externe necessaire.")
        print("\n=== RESUME ===")
        print("Declarations valides : 0 (aucun nouveau salarie)")
        print("Declarations invalides : 0")
        print("Termine !")
    else:
        time.sleep(1)
        lon_bureau, lat_bureau = geocoder_adresse(ADRESSE_BUREAU)
        print(f"Bureau geocode : lon={lon_bureau}, lat={lat_bureau}")

        nb_valide = 0
        nb_invalide = 0
        nb_echec = 0

        for emp in employes:
            id_salarie, nom, prenom, adresse, mode = emp

            time.sleep(1)
            lon_dom, lat_dom = geocoder_adresse(adresse)
            if lon_dom is None:
                print(f"Adresse non trouvee : {prenom} {nom}")
                nb_echec += 1
                continue

            distance_vol = haversine(lon_dom, lat_dom, lon_bureau, lat_bureau)
            distance_km = round(distance_vol * COEF_ROUTIER, 2)

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
        print(f"Adresses non geocodees : {nb_echec}")
        print("Termine !")