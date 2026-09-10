import os
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
# Defaut sds_postgres:5432 = nom/port du conteneur sur le reseau Docker interne
# (utilise quand ce script tourne dans une tache Kestra). Surcharger DB_HOST/DB_PORT
# via .env si ce script est plutot lance manuellement depuis l'hote.
DB_HOST = os.environ.get("DB_HOST", "sds_postgres")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "avantages_sportifs")

engine = create_engine(
    f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

def envoyer_message_slack(message):
    payload = {"text": message}
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    return response.status_code == 200

def formater_duree(duree_s):
    minutes = duree_s // 60
    return f"{minutes} min"

def formater_distance(distance_m):
    if distance_m is None:
        return None
    return round(distance_m / 1000, 1)

print("=== NOTIFICATIONS SLACK - Activites sportives ===\n")

with engine.connect() as conn:
    # Recuperer les activites les PLUS RECEMMENT INSEREES en base (created_at),
    # et non plus un tirage aleatoire parmi les 12 derniers mois. Ca garantit
    # qu'une activite tout juste ajoutee (ex. via demo_live.py) soit bien celle
    # notifiee en priorite - important pour la demonstration en direct.
    activites = conn.execute(text("""
        SELECT a.id, e.prenom, e.nom, a.type_sport, a.distance_m, a.duree_s, a.commentaire
        FROM activites_sportives a
        JOIN employes e ON a.id_salarie = e.id_salarie
        WHERE a.date_debut >= NOW() - INTERVAL '12 months'
        ORDER BY a.created_at DESC
        LIMIT 5
    """)).fetchall()

    nb_envoyes = 0
    for act in activites:
        id_act, prenom, nom, sport, distance_m, duree_s, commentaire = act

        distance_km = formater_distance(distance_m)
        duree = formater_duree(duree_s)

        if distance_km:
            message = f"Bravo {prenom} {nom} ! Tu viens de faire {sport} : {distance_km} km en {duree} ! Quelle energie ! 🔥🏅"
        else:
            message = f"Bravo {prenom} {nom} ! Tu viens de terminer une seance de {sport} en {duree} ! Super effort ! 💪"

        if commentaire:
            message += f"\n_{commentaire}_"

        if envoyer_message_slack(message):
            print(f" Message envoyé : {prenom} {nom} - {sport}")
            nb_envoyes += 1
        else:
            print(f" Erreur pour {prenom} {nom}")

print(f"\n{nb_envoyes} messages envoyés sur Slack !")