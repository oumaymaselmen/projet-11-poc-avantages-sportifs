# POC Avantages Sportifs - Sport Data Solution

Pipeline de donnees automatise pour le suivi des activites sportives des salaries et le calcul de deux avantages RH : une prime salariale de 5% pour les deplacements domicile-bureau a velo/a pied, et 5 jours de bien-etre supplementaires pour les salaries realisant au moins 15 activites sportives par an.

## Contexte

Ce POC repond a un besoin de Sport Data Solution : automatiser l'attribution d'avantages lies a l'activite sportive des 161 salaries, en croisant des donnees RH, des donnees d'activites type Strava, et une validation geographique des trajets declares.

## Architecture

- **Base de donnees** : PostgreSQL 15 (via Docker), 4 tables (employes, activites_sportives, avantages_calcules, distances_domicile_bureau) + une vue consolidee pour Power BI
- **Orchestration** : Kestra (flow pipeline_avantages_sportifs, declenchement quotidien par cron)
- **ORM** : SQLAlchemy + pilote pg8000
- **Validation geographique** : geocodage Nominatim (OpenStreetMap) + calcul de distance Haversine avec coefficient routier
- **Notifications** : Slack (Incoming Webhook)
- **Restitution** : Power BI Desktop

## Scripts

| Script | Role |
|---|---|
| generate_data.py | Genere ~7000 activites sportives simulees a partir des fichiers RH et Sportif |
| tests_qualite.py | 9 tests automatises de qualite des donnees |
| validation_distances.py | Valide le mode de transport declare via calcul de distance domicile-bureau |
| calcul_avantages.py | Calcule l'eligibilite aux deux avantages (avec verification des distances validees) |
| slack_notifications.py | Envoie des messages de felicitations sur Slack |
| demo_live.py | Script de demonstration : insere une activite en temps reel |

## Resultats

- **59 salaries eligibles** a la prime sportive - cout total : **152 434,50 EUR**
- **~140-142 salaries eligibles** aux jours de bien-etre supplementaires
- 9 adresses non geocodables (salaries non eligibles faute de verification possible)

## Choix techniques

- **Distances mises en cache** : les distances domicile-bureau ne sont calculees qu'une fois par salarie et conservees en base, evitant les appels externes redondants a chaque execution du pipeline
- **Nominatim + Haversine** plutot qu'une API a quota : solution sans limite de requetes, plus robuste pour un usage recurrent
- **Recalcul complet des avantages** a chaque execution (TRUNCATE + reinsertion), permettant de rejouer l'historique si le taux de prime ou les donnees sources changent

## Installation

```bash
git clone https://github.com/oumaymaselmen/projet-11-poc-avantages-sportifs.git
cd projet-11-poc-avantages-sportifs/infrastructure
docker-compose up -d
```

Creer un fichier .env a la racine avec : SLACK_WEBHOOK_URL, POSTGRES_PASSWORD, DB_HOST, DB_PORT

## Stack technique

Python - PostgreSQL - Docker - Kestra - SQLAlchemy - Power BI - Nominatim - Slack API

---
*Projet realise dans le cadre de la formation Data Engineer - OpenClassrooms*