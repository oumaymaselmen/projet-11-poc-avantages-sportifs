from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5435')

engine = create_engine(
    f"postgresql+pg8000://sds_admin:{os.getenv('POSTGRES_PASSWORD')}@{DB_HOST}:{DB_PORT}/avantages_sportifs"
)

TAUX_PRIME = 0.05

print("=== CALCUL DES AVANTAGES - POC Avantages Sportifs ===\n")
print(f"Taux de prime applique : {TAUX_PRIME * 100:.0f}%\n")

MODES_SPORTIFS = ["Vélo/Trottinette/Autres", "Marche/running"]

with engine.begin() as conn:

    conn.execute(text("TRUNCATE TABLE avantages_calcules RESTART IDENTITY"))

    employes = conn.execute(text("""
        SELECT e.id_salarie, e.salaire_brut, e.moyen_deplacement, d.declaration_valide
        FROM employes e
        LEFT JOIN distances_domicile_bureau d ON e.id_salarie = d.id_salarie
    """)).fetchall()

    nb_eligible_prime = 0
    nb_eligible_bienetre = 0
    nb_distance_non_validee = 0

    for emp in employes:
        id_salarie = emp[0]
        salaire_brut = float(emp[1])
        moyen_deplacement = emp[2]
        declaration_valide = emp[3]

        deplacement_sportif = moyen_deplacement in MODES_SPORTIFS

        if not deplacement_sportif:
            eligible_prime = False
            motif_prime = "Deplacement non sportif"
        elif declaration_valide is True:
            eligible_prime = True
            motif_prime = "Deplacement sportif declare et distance validee"
        else:
            eligible_prime = False
            motif_prime = "Distance domicile-bureau non validee"
            nb_distance_non_validee += 1

        montant_prime = round(salaire_brut * TAUX_PRIME, 2) if eligible_prime else 0
        if eligible_prime:
            nb_eligible_prime += 1

        nb_activites = conn.execute(text("""
            SELECT COUNT(*) FROM activites_sportives
            WHERE id_salarie = :id AND date_debut >= NOW() - INTERVAL '12 months'
        """), {"id": id_salarie}).scalar()

        eligible_bienetre = nb_activites >= 15
        nb_jours = 5 if eligible_bienetre else 0
        if eligible_bienetre:
            nb_eligible_bienetre += 1

        conn.execute(text("""
            INSERT INTO avantages_calcules
                (id_salarie, eligible_prime, motif_prime, montant_prime,
                 eligible_jours_bienetre, nb_activites_annee, nb_jours_bienetre)
            VALUES (:id_salarie, :eligible_prime, :motif_prime, :montant_prime,
                    :eligible_bienetre, :nb_activites, :nb_jours)
        """), {
            "id_salarie": id_salarie,
            "eligible_prime": eligible_prime,
            "motif_prime": motif_prime,
            "montant_prime": montant_prime,
            "eligible_bienetre": eligible_bienetre,
            "nb_activites": nb_activites,
            "nb_jours": nb_jours
        })

    cout_total_primes = conn.execute(text("SELECT SUM(montant_prime) FROM avantages_calcules")).scalar()

print(f"Salaries traites : {len(employes)}")
print(f"Eligibles a la prime sportive ({TAUX_PRIME*100:.0f}%) : {nb_eligible_prime}")
print(f"Dont deplacement sportif mais distance non validee : {nb_distance_non_validee}")
print(f"Eligibles aux 5 jours bien-etre : {nb_eligible_bienetre}")
print(f"Cout total des primes : {cout_total_primes:.2f} EUR")
print("\n=== Termine ===")