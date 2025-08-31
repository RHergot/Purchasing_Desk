-- =========================================================================
-- Script pour la création des tables du processus d'Appel d'Offres (AO)
-- Phase 2 de l'application "Purchasing Desk"
-- =========================================================================

-- On s'assure de travailler dans le bon schéma
SET search_path TO public;

-- Création des types ENUM pour les statuts du processus d'AO
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'statut_ao') THEN
        CREATE TYPE statut_ao AS ENUM ('Ouvert', 'Clos', 'Annulé', 'Archivé');
    END IF;
END$$;


-- =============================================
-- Table: appel_offre
-- Description: Le "dossier" principal de l'appel d'offres.
-- Il est lié à une 'commande' (brouillon) qui a initié le besoin.
-- =============================================
CREATE TABLE IF NOT EXISTS public.appel_offre (
    id_ao SERIAL PRIMARY KEY,
    -- Le lien crucial vers la commande qui a déclenché le besoin
    commande_id INTEGER NOT NULL UNIQUE REFERENCES public.commande(id_commande),
    reference_ao VARCHAR(50) UNIQUE NOT NULL,
    titre VARCHAR(255),
    createur_id INTEGER REFERENCES public.utilisateur(id_utilisateur),
    date_creation TIMESTAMPTZ DEFAULT NOW(),
    date_cloture_prevue TIMESTAMPTZ,
    statut statut_ao NOT NULL DEFAULT 'Ouvert'
);

COMMENT ON TABLE public.appel_offre IS 'Dossier central pour un appel d''offres.';
COMMENT ON COLUMN public.appel_offre.commande_id IS 'ID de la commande (brouillon) qui est à l''origine de cet AO.';


-- =============================================
-- Table: ao_fournisseur_consulte
-- Description: Table de liaison pour savoir quels fournisseurs ont été
-- contactés pour un appel d'offres spécifique.
-- =============================================
CREATE TABLE IF NOT EXISTS public.ao_fournisseur_consulte (
    id SERIAL PRIMARY KEY,
    ao_id INTEGER NOT NULL REFERENCES public.appel_offre(id_ao) ON DELETE CASCADE,
    fournisseur_id INTEGER NOT NULL REFERENCES public.fournisseur(id_fournisseur) ON DELETE CASCADE,
    date_envoi TIMESTAMPTZ,
    a_repondu BOOLEAN DEFAULT FALSE,
    UNIQUE (ao_id, fournisseur_id) -- On ne peut pas consulter le même fournisseur deux fois pour le même AO
);

COMMENT ON TABLE public.ao_fournisseur_consulte IS 'Liste des fournisseurs contactés pour un AO.';


-- =============================================
-- Table: offre_recue
-- Description: Enregistre la réponse globale d'un fournisseur à un AO.
-- =============================================
CREATE TABLE IF NOT EXISTS public.offre_recue (
    id_offre SERIAL PRIMARY KEY,
    ao_id INTEGER NOT NULL REFERENCES public.appel_offre(id_ao) ON DELETE CASCADE,
    fournisseur_id INTEGER NOT NULL REFERENCES public.fournisseur(id_fournisseur) ON DELETE CASCADE,
    date_reception TIMESTAMPTZ DEFAULT NOW(),
    reference_offre_fournisseur VARCHAR(100), -- Le numéro de devis du fournisseur
    delai_livraison_propose_j INTEGER,
    validite_offre_jours INTEGER,
    conditions_commerciales TEXT,
    UNIQUE (ao_id, fournisseur_id) -- Un fournisseur ne peut soumettre qu'une offre par AO
);

COMMENT ON TABLE public.offre_recue IS 'Réponse globale d''un fournisseur à un AO.';


-- =============================================
-- Table: offre_recue_ligne
-- Description: Le coeur du système. Contient le prix proposé par un
-- fournisseur pour une pièce spécifique dans le cadre d'une offre.
-- =============================================
CREATE TABLE IF NOT EXISTS public.offre_recue_ligne (
    id_offre_ligne SERIAL PRIMARY KEY,
    offre_id INTEGER NOT NULL REFERENCES public.offre_recue(id_offre) ON DELETE CASCADE,
    -- On ne lie pas à ligne_commande mais directement à la pièce pour plus de flexibilité
    piece_id INTEGER NOT NULL REFERENCES public.piece(id_piece),
    prix_unitaire_ht_propose DECIMAL(10, 4) NOT NULL, -- On utilise 4 décimales pour plus de précision
    remise_percent DECIMAL(5, 2) DEFAULT 0.00,
    commentaire TEXT,
    UNIQUE (offre_id, piece_id) -- Un seul prix par pièce et par offre
);

COMMENT ON TABLE public.offre_recue_ligne IS 'Détail des prix par pièce pour une offre fournisseur.';

-- =============================================
-- Fin du script de création
-- =============================================