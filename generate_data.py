import pandas as pd
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+pg8000://sds_admin:sportdata@sds_postgres:5432/avantages_sportifs"
)

with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
print("Connexion BDD OK")

df_rh = pd.read_excel("RH.xlsx")
df_sport = pd.read_excel("Sportive.xlsx")

df_rh.columns = [
    "id_salarie", "nom", "prenom", "date_naissance", "bu",
    "date_embauche", "salaire_brut", "type_contrat",
    "nb_jours_cp", "adresse_domicile", "moyen_deplacement"
]
df_sport.columns = ["id_salarie", "sport_pratique"]
df = df_rh.merge(df_sport, on="id_salarie", how="left")

def excel_date(val):
    try:
        if pd.isna(val): return None
        return (datetime(1899, 12, 30) + timedelta(days=int(val))).date()
    except: return None

df["date_naissance"] = df["date_naissance"].apply(excel_date)
df["date_embauche"] = df["date_embauche"].apply(excel_date)
df["id_salarie"] = df["id_salarie"].astype(int)
df["salaire_brut"] = df["salaire_brut"].astype(float)
df["sport_pratique"] = df["sport_pratique"].where(pd.notna(df["sport_pratique"]), None)

print(f"{len(df)} salaries charges")

with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE avantages_calcules, distances_domicile_bureau, activites_sportives, employes RESTART IDENTITY CASCADE"))
    for _, row in df.iterrows():
        conn.execute(text("""
            INSERT INTO employes (id_salarie, nom, prenom, date_naissance, bu, date_embauche,
                salaire_brut, type_contrat, nb_jours_cp, adresse_domicile, moyen_deplacement, sport_pratique)
            VALUES (:id_salarie, :nom, :prenom, :date_naissance, :bu, :date_embauche,
                :salaire_brut, :type_contrat, :nb_jours_cp, :adresse_domicile, :moyen_deplacement, :sport_pratique)
            ON CONFLICT (id_salarie) DO NOTHING
        """), {
            "id_salarie": int(row["id_salarie"]),
            "nom": row["nom"], "prenom": row["prenom"],
            "date_naissance": row["date_naissance"],
            "bu": row["bu"], "date_embauche": row["date_embauche"],
            "salaire_brut": float(row["salaire_brut"]),
            "type_contrat": row["type_contrat"],
            "nb_jours_cp": int(row["nb_jours_cp"]) if pd.notna(row["nb_jours_cp"]) else None,
            "adresse_domicile": row["adresse_domicile"],
            "moyen_deplacement": row["moyen_deplacement"],
            "sport_pratique": row["sport_pratique"] if pd.notna(row.get("sport_pratique")) else None
        })

print(f"{len(df)} salaries inseres")

SPORTS_AVEC_DISTANCE = {
    "Course a pied":  {"distance": (3000, 25000),  "vitesse_ms": (2.5, 4.5)},
    "Velo":           {"distance": (10000, 80000),  "vitesse_ms": (5.0, 10.0)},
    "Randonnee":      {"distance": (5000, 20000),   "vitesse_ms": (1.0, 1.8)},
    "Natation":       {"distance": (500, 3000),     "vitesse_ms": (0.8, 1.5)},
    "Marche":         {"distance": (2000, 10000),   "vitesse_ms": (1.2, 1.8)},
}
SPORTS_SANS_DISTANCE = ["Escalade", "Judo", "Rugby", "Football", "Basketball",
                        "Tennis", "Badminton", "Tennis de table", "Boxe", "Equitation", "Voile", "Triathlon"]
COMMENTAIRES = ["Super seance !", "Content de moi :)", "Nouveau record !", "Belle sortie",
                "Reprise du sport :)", "Conditions parfaites", None, None, None]

def get_sport(sport_declare):
    if pd.isna(sport_declare) or sport_declare is None:
        return random.choice(list(SPORTS_AVEC_DISTANCE.keys()))
    sport = str(sport_declare).strip()
    if sport in ["Runing", "Running"]: return "Course a pied"
    if sport in SPORTS_SANS_DISTANCE: return sport
    if sport in SPORTS_AVEC_DISTANCE: return sport
    return random.choice(list(SPORTS_AVEC_DISTANCE.keys()))

activites = []
date_fin_periode = datetime.now()
date_debut_periode = date_fin_periode - timedelta(days=365)

for _, emp in df.iterrows():
    id_salarie = int(emp["id_salarie"])
    sport = get_sport(emp.get("sport_pratique"))
    nb_activites = random.randint(5, 80)
    for _ in range(nb_activites):
        jours = random.randint(0, 365)
        date_debut = date_debut_periode + timedelta(days=jours)
        heure = random.choice([random.randint(6, 9), random.randint(17, 20)])
        date_debut = date_debut.replace(hour=heure, minute=random.randint(0, 59))
        if sport in SPORTS_AVEC_DISTANCE:
            params = SPORTS_AVEC_DISTANCE[sport]
            distance_m = random.randint(*params["distance"])
            vitesse = random.uniform(*params["vitesse_ms"])
            duree_s = int(distance_m / vitesse)
        else:
            distance_m = None
            duree_s = random.randint(1800, 7200)
        date_fin = date_debut + timedelta(seconds=duree_s)
        commentaire = random.choice(COMMENTAIRES)
        activites.append({
            "id_salarie": id_salarie, "date_debut": date_debut,
            "date_fin": date_fin, "type_sport": sport,
            "distance_m": distance_m, "duree_s": duree_s,
            "commentaire": commentaire, "source": "simulation"
        })

with engine.begin() as conn:
    conn.execute(text("""
        INSERT INTO activites_sportives
            (id_salarie, date_debut, date_fin, type_sport, distance_m, duree_s, commentaire, source)
        VALUES (:id_salarie, :date_debut, :date_fin, :type_sport, :distance_m, :duree_s, :commentaire, :source)
    """), activites)

print(f"{len(activites)} activites inserees")
print("Termine !")