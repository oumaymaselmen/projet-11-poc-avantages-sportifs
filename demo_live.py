from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+pg8000://sds_admin:sportdata@localhost:5435/avantages_sportifs"
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