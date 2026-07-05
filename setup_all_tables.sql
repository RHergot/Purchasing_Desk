-- ============================================================================
-- Purchasing Desk — Complete PostgreSQL Schema
-- Generated from SQLAlchemy models:
--   app/models/shared_models.py
--   app/models/purchase_models.py
-- All tables in schema 'public'.
-- ============================================================================

-- Make sure we're in the right search path
SET search_path TO public;

-- ============================================================================
-- 1. TABLES WITH NO FOREIGN KEY DEPENDENCIES
-- ============================================================================

-- ---------------------------------------------------------------------------
-- fournisseur
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fournisseur (
    id_fournisseur  SERIAL       PRIMARY KEY,
    nom             VARCHAR(100) NOT NULL,
    email           VARCHAR(100),
    adresse         TEXT,
    telephone       VARCHAR(50),
    devise          VARCHAR(10)  DEFAULT 'EUR'
);

-- ---------------------------------------------------------------------------
-- machine
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS machine (
    id_machine      SERIAL       PRIMARY KEY,
    nom             VARCHAR(100)
);

-- ---------------------------------------------------------------------------
-- utilisateur
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS utilisateur (
    id_utilisateur  SERIAL       PRIMARY KEY,
    nom_complet     VARCHAR(100),
    role            VARCHAR(50),
    email           VARCHAR(100) UNIQUE,
    login           VARCHAR(50)  UNIQUE
);

-- ============================================================================
-- 2. piece (FK → fournisseur)
-- ============================================================================

CREATE TABLE IF NOT EXISTS piece (
    id_piece            SERIAL          PRIMARY KEY,
    reference           VARCHAR(50)     UNIQUE NOT NULL,
    nom                 VARCHAR(255),                           -- SQLAlchemy: Column('nom',…), attribute 'designation'
    fournisseur_pref_id INTEGER         REFERENCES fournisseur(id_fournisseur),
                                                               -- SQLAlchemy: Column('fournisseur_pref_id',…), attribute 'fournisseur_id_default'
    prix_unitaire       NUMERIC(10, 2),                        -- SQLAlchemy: Column('prix_unitaire',…), attribute 'prix_achat_ht'
    statut              VARCHAR(50)     DEFAULT 'actif',
    categorie           VARCHAR(100),
    stock_actuel        INTEGER         DEFAULT 0,
    stock_alerte        INTEGER         DEFAULT 0,
    unite               VARCHAR(50)
);

-- ============================================================================
-- 3. piece_extension (FK → piece, machine)
-- ============================================================================

CREATE TABLE IF NOT EXISTS piece_extension (
    id_piece        INTEGER     PRIMARY KEY     REFERENCES piece(id_piece),
    unite_id        INTEGER,                        -- external FK (reference table not yet modelled)
    categorie_id    INTEGER,                        -- external FK (reference table not yet modelled)
    emplacement_id  INTEGER,                        -- external FK (reference table not yet modelled)
    statut_id       INTEGER,                        -- external FK (reference table not yet modelled)
    machine_id      INTEGER     REFERENCES machine(id_machine)
);

-- ============================================================================
-- 4. piece_fournisseur_info (FK → piece, fournisseur)
-- ============================================================================

CREATE TABLE IF NOT EXISTS piece_fournisseur_info (
    id_piece_fournisseur_info   SERIAL          PRIMARY KEY,
    piece_id                    INTEGER         NOT NULL    REFERENCES piece(id_piece),
    fournisseur_id              INTEGER         NOT NULL    REFERENCES fournisseur(id_fournisseur),

    reference_fournisseur       VARCHAR(100),
    prix_catalogue_fournisseur  NUMERIC(12, 4),
    devise_prix_catalogue       VARCHAR(10)     DEFAULT 'EUR',
    delai_livraison_standard_j  INTEGER,
    unite_achat_fournisseur     VARCHAR(50),
    quantite_min_commande       INTEGER,
    dernier_prix_negocie        NUMERIC(12, 4),
    date_dernier_prix_negocie   DATE,
    commentaire                 TEXT,
    actif                       BOOLEAN         DEFAULT TRUE,
    updated_at                  TIMESTAMPTZ     DEFAULT NOW(),

    CONSTRAINT uq_piece_fournisseur UNIQUE (piece_id, fournisseur_id)
);

-- ============================================================================
-- 5. commande (FK → fournisseur, utilisateur)
-- ============================================================================

CREATE TABLE IF NOT EXISTS commande (
    id_commande             SERIAL          PRIMARY KEY,
    numero_commande         TEXT,
    fournisseur_id          INTEGER         NOT NULL    REFERENCES fournisseur(id_fournisseur),
    createur_id             INTEGER         NOT NULL    REFERENCES utilisateur(id_utilisateur),
    date_commande           TIMESTAMP       NOT NULL,
    date_livraison_prevue   TIMESTAMP,
    statut                  VARCHAR(50)     NOT NULL    DEFAULT 'Brouillon',
    total_ht                NUMERIC(10, 2)  DEFAULT 0.0,

    CONSTRAINT ck_commande_statut CHECK (
        statut IN ('Brouillon', 'Validee', 'Envoyee', 'Partielle', 'Livree', 'Annulee')
    )
);

-- ============================================================================
-- 6. ligne_commande (FK → commande, piece)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ligne_commande (
    id_ligne            SERIAL          PRIMARY KEY,
    commande_id         INTEGER         NOT NULL    REFERENCES commande(id_commande),
    piece_id            INTEGER         NOT NULL    REFERENCES piece(id_piece),
    description_libre   TEXT,
    quantite_commandee  INTEGER         NOT NULL,
    prix_unitaire_ht    NUMERIC(10, 4)  NOT NULL,
    quantite_recue      INTEGER         DEFAULT 0,
    statut_ligne        VARCHAR(50)     NOT NULL    DEFAULT 'Attente',

    CONSTRAINT ck_ligne_commande_prix_ht   CHECK (prix_unitaire_ht >= 0),
    CONSTRAINT ck_ligne_commande_quantite  CHECK (quantite_commandee > 0),
    CONSTRAINT ck_ligne_commande_statut    CHECK (
        statut_ligne IN ('Attente', 'Partielle', 'Complete', 'Annulee')
    )
);

-- ============================================================================
-- 7. contrat_achat (FK → fournisseur, utilisateur)
-- ============================================================================

CREATE TABLE IF NOT EXISTS contrat_achat (
    id_contrat_achat                SERIAL          PRIMARY KEY,
    reference_interne_contrat       VARCHAR(50)     UNIQUE NOT NULL,
    objet_contrat                   TEXT            NOT NULL,
    fournisseur_id                  INTEGER         NOT NULL    REFERENCES fournisseur(id_fournisseur),

    numero_contrat_fournisseur      VARCHAR(100),

    date_signature                  DATE,
    date_debut_validite             DATE            NOT NULL,
    date_fin_validite               DATE            NOT NULL,
    date_prochain_renouvellement    DATE,

    montant_total_engage            NUMERIC(14, 2),
    devise_contrat                  VARCHAR(3)      DEFAULT 'EUR',

    type_contrat                    TEXT,
    statut_contrat                  VARCHAR(50)     NOT NULL    DEFAULT 'Actif',

    contact_principal_achat_id      INTEGER         REFERENCES utilisateur(id_utilisateur),
    contact_fournisseur_specifique  TEXT,

    chemin_document_pdf             TEXT,
    notes_contrat                   TEXT,

    created_at                      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ     DEFAULT NOW(),

    CONSTRAINT ck_contrat_achat_statut CHECK (
        statut_contrat IN ('Brouillon', 'Actif', 'Expiré', 'Renouvelé', 'Annulé', 'Archivé')
    )
);

-- ============================================================================
-- 8. appel_offre (FK → commande, utilisateur)
-- ============================================================================

CREATE TABLE IF NOT EXISTS appel_offre (
    id_ao                   SERIAL          PRIMARY KEY,
    commande_id             INTEGER         NOT NULL    UNIQUE  REFERENCES commande(id_commande),
    reference_ao            VARCHAR(50)     UNIQUE NOT NULL,
    titre                   VARCHAR(255),
    createur_id             INTEGER         REFERENCES utilisateur(id_utilisateur),
    date_creation           TIMESTAMPTZ     DEFAULT NOW(),
    date_cloture_prevue     TIMESTAMPTZ,
    statut                  VARCHAR(50)     NOT NULL    DEFAULT 'Ouvert',

    CONSTRAINT ck_appel_offre_statut CHECK (
        statut IN ('Ouvert', 'Clos', 'Annulé', 'Archivé')
    )
);

-- ============================================================================
-- 9. ao_fournisseur_consulte (FK → appel_offre, fournisseur)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ao_fournisseur_consulte (
    id              SERIAL      PRIMARY KEY,
    ao_id           INTEGER     NOT NULL    REFERENCES appel_offre(id_ao),
    fournisseur_id  INTEGER     NOT NULL    REFERENCES fournisseur(id_fournisseur),
    date_envoi      TIMESTAMPTZ,
    a_repondu       BOOLEAN     DEFAULT FALSE,

    CONSTRAINT uq_ao_fournisseur UNIQUE (ao_id, fournisseur_id)
);

-- ============================================================================
-- 10. offre_recue (FK → appel_offre, fournisseur)
-- ============================================================================

CREATE TABLE IF NOT EXISTS offre_recue (
    id_offre                    SERIAL          PRIMARY KEY,
    ao_id                       INTEGER         NOT NULL    REFERENCES appel_offre(id_ao),
    fournisseur_id              INTEGER         NOT NULL    REFERENCES fournisseur(id_fournisseur),
    date_reception              TIMESTAMPTZ     DEFAULT NOW(),
    reference_offre_fournisseur VARCHAR(100),
    delai_livraison_propose_j   INTEGER,
    validite_offre_jours        INTEGER,
    conditions_commerciales     TEXT
);

-- ============================================================================
-- 11. offre_recue_ligne (FK → offre_recue, piece)
-- ============================================================================

CREATE TABLE IF NOT EXISTS offre_recue_ligne (
    id_offre_ligne              SERIAL          PRIMARY KEY,
    offre_id                    INTEGER         NOT NULL    REFERENCES offre_recue(id_offre),
    piece_id                    INTEGER         NOT NULL    REFERENCES piece(id_piece),
    prix_unitaire_ht_propose    NUMERIC(10, 4)  NOT NULL,
    remise_percent              NUMERIC(5, 2)   DEFAULT 0.00,
    commentaire                 TEXT
);

-- ============================================================================
-- 12. prestation_achat (FK → maintenance*, utilisateur, contrat_achat, fournisseur, commande)
--    * maintenance.id_maintenance is an external GMAO table, not modelled here.
-- ============================================================================

CREATE TABLE IF NOT EXISTS prestation_achat (
    id_prestation_achat             SERIAL          PRIMARY KEY,
    reference_prestation            VARCHAR(50)     UNIQUE,

    -- External GMAO reference (table 'maintenance' not created by this script)
    maintenance_id                  INTEGER,        -- REFERENCES maintenance(id_maintenance)

    description_besoin              TEXT            NOT NULL,
    type_prestation                 VARCHAR(50)     NOT NULL,
    statut_prestation               VARCHAR(50)     NOT NULL    DEFAULT 'DEMANDE_INITIALE',
    urgence                         BOOLEAN         DEFAULT FALSE,

    demandeur_maintenance_id        INTEGER         REFERENCES utilisateur(id_utilisateur),
    date_demande                    TIMESTAMPTZ     DEFAULT NOW(),
    acheteur_responsable_id         INTEGER         REFERENCES utilisateur(id_utilisateur),

    sous_contrat                    BOOLEAN         DEFAULT FALSE,
    contrat_achat_id                INTEGER         REFERENCES contrat_achat(id_contrat_achat),
    reference_contrat_fournisseur   TEXT,

    fournisseur_id                  INTEGER         REFERENCES fournisseur(id_fournisseur),
    contact_fournisseur_prestation  TEXT,

    montant_estime_demande          NUMERIC(12, 2),
    devise_estimation               VARCHAR(3)      DEFAULT 'EUR',
    commande_initiale_id            INTEGER         REFERENCES commande(id_commande),

    description_travaux_reels       TEXT,
    montant_facture_final           NUMERIC(12, 2),
    devise_facture                  VARCHAR(3),
    reference_facture_fournisseur   TEXT,
    date_reception_facture          DATE,
    notes_facturation               TEXT,

    necessite_regularisation        BOOLEAN         DEFAULT FALSE,
    commande_regularisation_id      INTEGER         REFERENCES commande(id_commande),
    montant_regularisation_calcule  NUMERIC(12, 2),

    notes_generales                 TEXT,
    created_at                      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ     DEFAULT NOW(),

    CONSTRAINT ck_prestation_achat_type   CHECK (
        type_prestation IN (
            'SERVICE_MAINTENANCE',
            'PIECE_HORS_CATALOGUE',
            'CONSULTATION_EXTERNE',
            'FORMATION',
            'SOUS_TRAITANCE_FORFAIT',
            'FRAIS_DEPLACEMENT',
            'AUTRE_SERVICE'
        )
    ),
    CONSTRAINT ck_prestation_achat_statut CHECK (
        statut_prestation IN (
            'DEMANDE_INITIALE',
            'EN_DEVIS',
            'OFFRE_ANALYSE',
            'COMMANDE_A_EMETTRE',
            'COMMANDE_EMISE',
            'PRESTATION_EN_COURS',
            'PRESTATION_TERMINEE',
            'FACTURE_RECUE',
            'ATTENTE_REGULARISATION',
            'REGULARISATION_EMISE',
            'CLOS',
            'ANNULEE'
        )
    )
);

-- ============================================================================
-- OPTIONAL: trigger to auto-update updated_at columns
-- Uncomment if you want automatic timestamp tracking without relying on the ORM.
-- ============================================================================

/*
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_piece_fournisseur_info_updated_at
    BEFORE UPDATE ON piece_fournisseur_info
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_contrat_achat_updated_at
    BEFORE UPDATE ON contrat_achat
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_prestation_achat_updated_at
    BEFORE UPDATE ON prestation_achat
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
*/

-- ============================================================================
-- Summary of tables created (14):
--   1.  fournisseur
--   2.  machine
--   3.  utilisateur
--   4.  piece
--   5.  piece_extension
--   6.  piece_fournisseur_info
--   7.  commande
--   8.  ligne_commande
--   9.  contrat_achat
--   10. appel_offre
--   11. ao_fournisseur_consulte
--   12. offre_recue
--   13. offre_recue_ligne
--   14. prestation_achat
-- ============================================================================
