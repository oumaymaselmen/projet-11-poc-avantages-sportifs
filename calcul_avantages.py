from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+pg8000://sds_admin:sportdata@sds_postgres:5432/avantages_sportifs"
)

print("=== CALCUL DES AVANTAGES - POC Avantages Sportifs ===\n")

# Modes de deplacement consideres comme "sportifs" pour la prime
MODES_SPORTIFS = ["Vélo/Trottinette/Autres", "Marche/running"]
with engine.begin() as conn:

    # Vider la table avant recalcul (pour pouvoir relancer si les parametres changent)
    conn.execute(text("TRUNCATE TABLE avantages_calcules RESTART IDENTITY"))

    employes = conn.execute(text("SELECT id_salarie, salaire_brut, moyen_deplacement FROM employes")).fetchall()

    nb_eligible_prime = 0
    nb_eligible_bienetre = 0

    for emp in employes:
        id_salarie = emp[0]
        salaire_brut = float(emp[1])
        moyen_deplacement = emp[2]

        # --- PRIME SPORTIVE (5% du salaire) ---
        eligible_prime = moyen_deplacement in MODES_SPORTIFS
        montant_prime = round(salaire_brut * 0.05, 2) if eligible_prime else 0
        motif_prime = "Deplacement sportif declare" if eligible_prime else "Deplacement non sportif"
        if eligible_prime:
            nb_eligible_prime += 1

        # --- JOURS BIEN-ETRE (5 jours si >= 15 activites/an) ---
        nb_activites = conn.execute(text("""
            SELECT COUNT(*) FROM activites_sportives
            WHERE id_salarie = :id AND date_debut >= NOW() - INTERVAL '12 months'
        """), {"id": id_salarie}).scalar()

        eligible_bienetre = nb_activites >= 15
        nb_jours = 5 if eligible_bienetre else 0
        if eligible_bienetre:
            nb_eligible_bienetre += 1

        # Insertion du resultat
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

    # Impact financier total
    cout_total_primes = conn.execute(text("SELECT SUM(montant_prime) FROM avantages_calcules")).scalar()

print(f"Salaries traites : {len(employes)}")
print(f"Eligibles a la prime sportive (5%) : {nb_eligible_prime}")
print(f"Eligibles aux 5 jours bien-etre : {nb_eligible_bienetre}")
print(f"Cout total des primes : {cout_total_primes:.2f} EUR")
print("\n=== Termine ===")