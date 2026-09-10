import os
import time
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5435")
DB_NAME = os.environ.get("DB_NAME", "avantages_sportifs")
GOOGLE_MAPS_API_KEY = os.environ["GOOGLE_MAPS_API_KEY"]

engine = create_engine(
    f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

ADRESSE_BUREAU = "1362 Avenue des Platanes, 34970 Lattes, France"

DISTANCE_MAX = {
    "Marche/running": 15,
    "Vélo/Trottinette/Autres": 25,
}

# Mode de déplacement Google Maps le plus proche pour chaque déclaration
MODE_GOOGLE = {
    "Marche/running": "walking",
    "Vélo/Trottinette/Autres": "bicycling",
}


def distance_routiere_km(adresse_domicile, mode_google):
    """Distance routière réelle (km) entre le domicile et le bureau via
    l'API Google Maps Distance Matrix. Retourne None si l'adresse ou
    l'itinéraire n'est pas trouvé."""
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": adresse_domicile,
        "destinations": ADRESSE_BUREAU,
        "mode": mode_google,
        "units": "metric",
        "key": GOOGLE_MAPS_API_KEY,
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get("status") != "OK":
            print(f"Erreur API Google Maps : {data.get('status')}")
            return None
        element = data["rows"][0]["elements"][0]
        if element.get("status") != "OK":
            print(f"Itineraire introuvable ({element.get('status')}) pour : {adresse_domicile}")
            return None
        return round(element["distance"]["value"] / 1000, 2)
    except Exception as e:
        print(f"Erreur appel Google Maps : {e}")
        return None


print("=== VALIDATION DISTANCES DOMICILE/BUREAU (API Google Maps) ===\n")

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
        nb_valide = 0
        nb_invalide = 0
        nb_echec = 0

        for emp in employes:
            id_salarie, nom, prenom, adresse, mode = emp
            mode_google = MODE_GOOGLE[mode]

            distance_km = distance_routiere_km(adresse, mode_google)
            time.sleep(0.2)  # marge de securite face au quota de l'API

            if distance_km is None:
                print(f"Adresse ou itineraire non trouve : {prenom} {nom}")
                nb_echec += 1
                continue

            distance_max = DISTANCE_MAX[mode]
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
        print(f"Adresses/itineraires non trouves : {nb_echec}")
        print("Termine !")