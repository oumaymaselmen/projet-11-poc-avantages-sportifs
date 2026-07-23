# 🏃 POC Avantages Sportifs — Sport Data Solution

Pipeline de données automatisé pour le suivi des activités sportives des salariés et le calcul de deux avantages RH : une prime salariale de 5% pour les déplacements domicile-bureau à vélo/à pied, et 5 jours de bien-être supplémentaires pour les salariés réalisant au moins 15 activités sportives par an.

## 🎯 Contexte

Ce POC répond à un besoin de Sport Data Solution : automatiser l'attribution d'avantages liés à l'activité sportive des 161 salariés, en croisant des données RH, des données d'activités type Strava, et une validation géographique des trajets déclarés.

## 🏗️ Architecture

- **Base de données** : PostgreSQL 15 (via Docker), 4 tables (`employes`, `activites_sportives`, `avantages_calcules`, `distances_domicile_bureau`) + une vue consolidée pour Power BI
- **Orchestration** : Kestra (flow `pipeline_avantages_sportifs`, déclenchement quotidien par cron)
- **ORM** : SQLAlchemy + pilote pg8000
- **Validation géographique** : API OpenRouteService (géocodage + calcul d'itinéraire)
- **Notifications** : Slack (Incoming Webhook)
- **Restitution** : Power BI Desktop

## 📂 Scripts

| Script | Rôle |
|---|---|
| `generate_data.py` | Génère ~7000 activités sportives simulées à partir des fichiers RH et Sportif |
| `tests_qualite.py` | 9 tests automatisés de qualité des données |
| `validation_distances.py` | Valide le mode de transport déclaré via calcul de distance réelle (OpenRouteService) |
| `calcul_avantages.py` | Calcule l'éligibilité aux deux avantages |
| `slack_notifications.py` | Envoie des messages de félicitations sur Slack |
| `demo_live.py` | Script de démonstration : insère une activité en temps réel pour déclencher le pipeline complet |

## 📊 Résultats

- **68 salariés éligibles** à la prime sportive — coût total : **172 482 €**
- **~142-146 salariés éligibles** aux jours de bien-être supplémentaires

## ⚙️ Installation

```bash
git clone https://github.com/oumaymaselmen/projet-11-poc-avantages-sportifs.git
cd projet-11-poc-avantages-sportifs
cd infrastructure
docker-compose up -d
```

## 🛠️ Stack technique

`Python` `PostgreSQL` `Docker` `Kestra` `SQLAlchemy` `Power BI` `OpenRouteService API` `Slack API`

---
*Projet réalisé dans le cadre de la formation Data Engineer — OpenClassrooms*
