-- ============================================================
-- POC Avantages Sportifs — Sport Data Solution
-- Script d'initialisation de la base de données
-- ============================================================

CREATE ROLE sds_readonly;
GRANT CONNECT ON DATABASE avantages_sportifs TO sds_readonly;
GRANT USAGE ON SCHEMA public TO sds_readonly;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- TABLE 1 : employes
CREATE TABLE IF NOT EXISTS employes (
    id                      SERIAL PRIMARY KEY,
    id_salarie              INTEGER NOT NULL UNIQUE,
    nom                     VARCHAR(100) NOT NULL,
    prenom                  VARCHAR(100) NOT NULL,
    date_naissance          DATE,
    bu                      VARCHAR(50),
    date_embauche           DATE,
    salaire_brut            NUMERIC(10, 2) NOT NULL,
    type_contrat            VARCHAR(10) CHECK (type_contrat IN ('CDI', 'CDD')),
    nb_jours_cp             INTEGER,
    adresse_domicile        TEXT,
    moyen_deplacement       VARCHAR(50),
    sport_pratique          VARCHAR(100),
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW()
);

-- TABLE 2 : activites_sportives
CREATE TABLE IF NOT EXISTS activites_sportives (
    id                      SERIAL PRIMARY KEY,
    id_salarie              INTEGER NOT NULL REFERENCES employes(id_salarie),
    date_debut              TIMESTAMP NOT NULL,
    date_fin                TIMESTAMP,
    type_sport              VARCHAR(50) NOT NULL,
    distance_m              INTEGER,
    duree_s                 INTEGER,
    commentaire             TEXT,
    source                  VARCHAR(20) DEFAULT 'simulation' CHECK (source IN ('simulation', 'strava', 'manuel')),
    created_at              TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_activites_id_salarie ON activites_sportives(id_salarie);
CREATE INDEX idx_activites_date ON activites_sportives(date_debut);

-- TABLE 3 : distances_domicile_bureau
CREATE TABLE IF NOT EXISTS distances_domicile_bureau (
    id                      SERIAL PRIMARY KEY,
    id_salarie              INTEGER NOT NULL REFERENCES employes(id_salarie) UNIQUE,
    adresse_domicile        TEXT NOT NULL,
    distance_km             NUMERIC(6, 2),
    mode_transport_declare  VARCHAR(50),
    distance_max_km         NUMERIC(6, 2),
    declaration_valide      BOOLEAN,
    motif_invalide          TEXT,
    date_verification       TIMESTAMP DEFAULT NOW()
);

-- TABLE 4 : avantages_calcules
CREATE TABLE IF NOT EXISTS avantages_calcules (
    id                      SERIAL PRIMARY KEY,
    id_salarie              INTEGER NOT NULL REFERENCES employes(id_salarie) UNIQUE,
    eligible_prime          BOOLEAN DEFAULT FALSE,
    motif_prime             TEXT,
    montant_prime           NUMERIC(10, 2),
    eligible_jours_bienetre BOOLEAN DEFAULT FALSE,
    nb_activites_annee      INTEGER DEFAULT 0,
    nb_jours_bienetre       INTEGER DEFAULT 0,
    annee_calcul            INTEGER DEFAULT EXTRACT(YEAR FROM NOW()),
    date_calcul             TIMESTAMP DEFAULT NOW(),
    date_mise_a_jour        TIMESTAMP DEFAULT NOW()
);

-- VUE pour Power BI
CREATE OR REPLACE VIEW vue_recap_avantages AS
SELECT
    e.id_salarie, e.nom, e.prenom, e.bu, e.salaire_brut,
    e.moyen_deplacement, e.sport_pratique,
    d.distance_km, d.declaration_valide,
    a.eligible_prime, a.montant_prime,
    a.eligible_jours_bienetre, a.nb_activites_annee,
    a.nb_jours_bienetre, a.annee_calcul
FROM employes e
LEFT JOIN distances_domicile_bureau d ON e.id_salarie = d.id_salarie
LEFT JOIN avantages_calcules a ON e.id_salarie = a.id_salarie;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO sds_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO sds_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO sds_readonly;