import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
# Meme remarque que slack_notifications.py : sds_postgres:5432 par defaut
# (reseau Docker interne, execution via Kestra a confirmer)
DB_HOST = os.environ.get("DB_HOST", "sds_postgres")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "avantages_sportifs")

engine = create_engine(
    f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
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

    nb_sans_act = conn.execute(text("SELECT COUNT(*) FROM employes e WHERE NOT EXISTS (SELECT 1 FROM activites_sportives a WHERE a.id_salarie = e.id_salarie)")).scalar()
    test("Tous les salaries ont des activites", nb_sans_act == 0, f"({nb_sans_act} salaries sans activite)")

    nb_sport = conn.execute(text("SELECT COUNT(*) FROM activites_sportives WHERE type_sport IS NULL OR type_sport = ''")).scalar()
    test("Types de sport non nuls", nb_sport == 0, f"({nb_sport} anomalies)")

print(f"\n=== RESUME ===")
nb_pass = sum(1 for r in resultats if r["pass"])
print(f"Tests reussis : {nb_pass}/{len(resultats)}")