import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5435")
DB_NAME = os.environ.get("DB_NAME", "avantages_sportifs")

engine = create_engine(
    f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

print("=== DEMO LIVE - Ajout d'une nouvelle activite ===\n")

with engine.begin() as conn:
    emp = conn.execute(text("""
        SELECT id_salarie, prenom, nom FROM employes ORDER BY RANDOM() LIMIT 1
    """)).fetchone()

    id_salarie = emp[0]
    prenom = emp[1]
    nom = emp[2]

    conn.execute(text("""
        INSERT INTO activites_sportives 
            (id_salarie, date_debut, date_fin, type_sport, distance_m, duree_s, commentaire, source)
        VALUES (:id_salarie, NOW(), NOW() + INTERVAL '3000 seconds',
                'Course a pied', 10000, 3000, 'Activite de demonstration', 'manuel')
    """), {"id_salarie": id_salarie})

print(f"Salarie : {prenom} {nom}")
print(f"Activite ajoutee : Course a pied - 10 km - 50 min")
print(f"\nLe pipeline Kestra va maintenant traiter cette activite.")