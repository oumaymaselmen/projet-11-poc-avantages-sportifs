from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+pg8000://sds_admin:sportdata@sds_postgres:5432/avantages_sportifs"
)


print("=== TESTS QUALITE - POC Avantages Sportifs ===\n")

resultats = []

def test(nom, resultat, details=""):
    statut = " PASS" if resultat else " FAIL"
    print(f"{statut} | {nom} {details}")
    resultats.append({"test": nom, "pass": resultat})

with engine.connect() as conn:

    nb = conn.execute(text("SELECT COUNT(*) FROM employes")).scalar()
    test("Table employes non vide", nb > 0, f"({nb} lignes)")

    nb_sal = conn.execute(text("SELECT COUNT(*) FROM employes WHERE salaire_brut <= 0")).scalar()
    test("Salaires tous positifs", nb_sal == 0, f"({nb_sal} anomalies)")

    nb_dup = conn.execute(text("SELECT COUNT(*) FROM (SELECT id_salarie, COUNT(*) FROM employes GROUP BY id_salarie HAVING COUNT(*) > 1) t")).scalar()
    test("Pas de doublon id_salarie", nb_dup == 0, f"({nb_dup} doublons)")

    nb_contrat = conn.execute(text("SELECT COUNT(*) FROM employes WHERE type_contrat NOT IN ('CDI', 'CDD')")).scalar()
    test("Type contrat valide CDI/CDD", nb_contrat == 0, f"({nb_contrat} anomalies)")

    nb_act = conn.execute(text("SELECT COUNT(*) FROM activites_sportives")).scalar()
    test("Table activites non vide", nb_act > 0, f"({nb_act} lignes)")

    nb_dist = conn.execute(text("SELECT COUNT(*) FROM activites_sportives WHERE distance_m IS NOT NULL AND distance_m < 0")).scalar()
    test("Distances non negatives", nb_dist == 0, f"({nb_dist} anomalies)")

    nb_duree = conn.execute(text("SELECT COUNT(*) FROM activites_sportives WHERE duree_s <= 0")).scalar()
    test("Durees toutes positives", nb_duree == 0, f"({nb_duree} anomalies)")

    nb_dates = conn.execute(text("SELECT COUNT(*) FROM activites_sportives WHERE date_debut < NOW() - INTERVAL '14 months' OR date_debut > NOW()")).scalar()

    nb_sans_act = conn.execute(text("SELECT COUNT(*) FROM employes e WHERE NOT EXISTS (SELECT 1 FROM activites_sportives a WHERE a.id_salarie = e.id_salarie)")).scalar()
    test("Tous les salaries ont des activites", nb_sans_act == 0, f"({nb_sans_act} salaries sans activite)")

    nb_sport = conn.execute(text("SELECT COUNT(*) FROM activites_sportives WHERE type_sport IS NULL OR type_sport = ''")).scalar()
    test("Types de sport non nuls", nb_sport == 0, f"({nb_sport} anomalies)")

print(f"\n=== RESUME ===")
nb_pass = sum(1 for r in resultats if r["pass"])
print(f"Tests reussis : {nb_pass}/{len(resultats)}")