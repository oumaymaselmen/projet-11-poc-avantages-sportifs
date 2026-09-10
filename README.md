# POC Avantages Sportifs - Sport Data Solution

Pipeline de donnees automatise pour le suivi des activites sportives des salaries et le calcul de deux avantages RH : une prime salariale de 5% pour les deplacements domicile-bureau a velo/a pied, et 5 jours de bien-etre supplementaires pour les salaries realisant au moins 15 activites sportives par an.

## Contexte

Ce POC repond a un besoin de Sport Data Solution : automatiser l'attribution d'avantages lies a l'activite sportive des 161 salaries, en croisant des donnees RH, des donnees d'activites type Strava, et une validation geographique des trajets declares.

## Architecture

- **Base de donnees** : PostgreSQL 15 (via Docker), 4 tables (employes, activites_sportives, avantages_calcules, distances_domicile_bureau) + une vue consolidee pour Power BI
- **Orchestration** : Kestra (flow pipeline_avantages_sportifs, declenchement quotidien par cron)
- **ORM** : SQLAlchemy + pilote pg8000
- **Validation geographique** : API Google Maps Distance Matrix (distance routiere reelle en mode marche/velo selon le deplacement declare)
- **Notifications** : Slack (Incoming Webhook)
- **Restitution** : Power BI Desktop

## Scripts

| Script | Role |
|---|---|
| generate_data.py | Genere ~7000 activites sportives simulees a partir des fichiers RH et Sportif |
| tests_qualite.py | 9 tests automatises de qualite des donnees |
| validation_distances.py | Valide le mode de transport declare via l'API Google Maps Distance Matrix |
| calcul_avantages.py | Calcule l'eligibilite aux deux avantages (avec verification des distances validees) |
| slack_notifications.py | Envoie des messages de felicitations sur Slack |
| demo_live.py | Script de demonstration : insere une activite en temps reel |
| check_all.py | Compte les lignes de chaque table (verification rapide) |
| check_db.py | Verifie le contenu de la table distances_domicile_bureau |

## Resultats

- **68 salaries eligibles** a la prime sportive - cout total : **172 482,50 EUR**
- **~130-140 salaries eligibles** aux jours de bien-etre supplementaires (le nombre varie legerement a chaque execution : l'eligibilite se base sur une fenetre glissante des 12 derniers mois)
- Toutes les declarations de deplacement actif ont ete validees par l'API Google Maps

## Choix techniques

- **Distances mises en cache** : les distances domicile-bureau ne sont calculees qu'une fois par salarie et conservees en base, evitant les appels externes redondants a chaque execution du pipeline
- **API Google Maps Distance Matrix** : conforme a la demande de la note de cadrage, donne une distance routiere reelle (et non une approximation a vol d'oiseau). Necessite une cle API avec facturation active sur Google Cloud (volume du POC couvert par le quota gratuit mensuel)
- **Recalcul complet des avantages** a chaque execution (TRUNCATE + reinsertion), permettant de rejouer l'historique si le taux de prime ou les donnees sources changent

## Installation

```bash
git clone https://github.com/oumaymaselmen/projet-11-poc-avantages-sportifs.git
cd projet-11-poc-avantages-sportifs
pip install -r requirements.txt
cd infrastructure
docker-compose up -d
```

Creer un fichier `.env` a la racine du projet (voir `.env.example`) avec :
`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `SLACK_WEBHOOK_URL`, `GOOGLE_MAPS_API_KEY`

## Stack technique

Python - PostgreSQL - Docker - Kestra - SQLAlchemy - Power BI - API Google Maps - Slack API

---
