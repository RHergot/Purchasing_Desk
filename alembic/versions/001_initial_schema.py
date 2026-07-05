"""Initial database schema — creates all Purchasing Desk tables.

Revision ID: 001
Revises: None
Create Date: 2026-07-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enums as CHECK constraints ──

    # statut_commande
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE statut_commande AS ENUM (
                'Brouillon', 'Validee', 'Envoyee', 'Partielle', 'Livree', 'Annulee'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # statut_ligne_commande
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE statut_ligne_commande AS ENUM (
                'Attente', 'Partielle', 'Complete', 'Annulee'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # statut_ao
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE statut_ao AS ENUM (
                'Ouvert', 'Clos', 'Annulé', 'Archivé'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # statut_contrat
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE statut_contrat AS ENUM (
                'Brouillon', 'Actif', 'Expiré', 'Renouvelé', 'Annulé', 'Archivé'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # type_prestation
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE type_prestation AS ENUM (
                'SERVICE_MAINTENANCE', 'PIECE_HORS_CATALOGUE',
                'CONSULTATION_EXTERNE', 'FORMATION', 'SOUS_TRAITANCE_FORFAIT',
                'FRAIS_DEPLACEMENT', 'AUTRE_SERVICE'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # statut_prestation
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE statut_prestation AS ENUM (
                'DEMANDE_INITIALE', 'EN_DEVIS', 'OFFRE_ANALYSE',
                'COMMANDE_A_EMETTRE', 'COMMANDE_EMISE', 'PRESTATION_EN_COURS',
                'PRESTATION_TERMINEE', 'FACTURE_RECUE', 'ATTENTE_REGULARISATION',
                'REGULARISATION_EMISE', 'CLOS', 'ANNULEE'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ── Tables ──

    op.create_table(
        "fournisseur",
        sa.Column("id_fournisseur", sa.Integer, primary_key=True),
        sa.Column("nom", sa.String(100), nullable=False),
        sa.Column("email", sa.String(100)),
        sa.Column("adresse", sa.Text),
        sa.Column("telephone", sa.String(50)),
        sa.Column("devise", sa.String(10), server_default="EUR"),
        schema="public",
    )

    op.create_table(
        "machine",
        sa.Column("id_machine", sa.Integer, primary_key=True),
        sa.Column("nom", sa.String(100)),
        schema="public",
    )

    op.create_table(
        "utilisateur",
        sa.Column("id_utilisateur", sa.Integer, primary_key=True),
        sa.Column("nom_complet", sa.String(100)),
        sa.Column("role", sa.String(50)),
        sa.Column("email", sa.String(100), unique=True),
        sa.Column("login", sa.String(50), unique=True),
        schema="public",
    )

    op.create_table(
        "piece",
        sa.Column("id_piece", sa.Integer, primary_key=True),
        sa.Column("reference", sa.String(50), unique=True, nullable=False),
        sa.Column("nom", sa.String(255)),
        sa.Column("fournisseur_pref_id", sa.Integer, sa.ForeignKey("public.fournisseur.id_fournisseur")),
        sa.Column("prix_unitaire", sa.Numeric(10, 2)),
        sa.Column("statut", sa.String(50), server_default="actif"),
        sa.Column("categorie", sa.String(100)),
        sa.Column("stock_actuel", sa.Integer, server_default="0"),
        sa.Column("stock_alerte", sa.Integer, server_default="0"),
        sa.Column("unite", sa.String(50)),
        schema="public",
    )

    op.create_table(
        "piece_extension",
        sa.Column("id_piece", sa.Integer, sa.ForeignKey("public.piece.id_piece"), primary_key=True),
        sa.Column("unite_id", sa.Integer),
        sa.Column("categorie_id", sa.Integer),
        sa.Column("emplacement_id", sa.Integer),
        sa.Column("statut_id", sa.Integer),
        sa.Column("machine_id", sa.Integer, sa.ForeignKey("public.machine.id_machine")),
        schema="public",
    )

    op.create_table(
        "piece_fournisseur_info",
        sa.Column("id_piece_fournisseur_info", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("piece_id", sa.Integer, sa.ForeignKey("public.piece.id_piece"), nullable=False),
        sa.Column("fournisseur_id", sa.Integer, sa.ForeignKey("public.fournisseur.id_fournisseur"), nullable=False),
        sa.Column("reference_fournisseur", sa.String(100)),
        sa.Column("prix_catalogue_fournisseur", sa.Numeric(12, 4)),
        sa.Column("devise_prix_catalogue", sa.String(10), server_default="EUR"),
        sa.Column("delai_livraison_standard_j", sa.Integer),
        sa.Column("unite_achat_fournisseur", sa.String(50)),
        sa.Column("quantite_min_commande", sa.Integer),
        sa.Column("dernier_prix_negocie", sa.Numeric(12, 4)),
        sa.Column("date_dernier_prix_negocie", sa.Date),
        sa.Column("commentaire", sa.Text),
        sa.Column("actif", sa.Boolean, server_default=sa.text("true")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("piece_id", "fournisseur_id", name="uq_piece_fournisseur"),
        schema="public",
    )

    op.create_table(
        "commande",
        sa.Column("id_commande", sa.Integer, primary_key=True),
        sa.Column("numero_commande", sa.Text),
        sa.Column("fournisseur_id", sa.Integer, sa.ForeignKey("public.fournisseur.id_fournisseur"), nullable=False),
        sa.Column("createur_id", sa.Integer, sa.ForeignKey("public.utilisateur.id_utilisateur"), nullable=False),
        sa.Column("date_commande", sa.DateTime, nullable=False),
        sa.Column("date_livraison_prevue", sa.DateTime),
        sa.Column("statut", sa.Enum("Brouillon", "Validee", "Envoyee", "Partielle", "Livree", "Annulee", name="statut_commande"), nullable=False, server_default="Brouillon"),
        sa.Column("total_ht", sa.Numeric(10, 2), server_default="0"),
        sa.CheckConstraint("statut IN ('Brouillon', 'Validee', 'Envoyee', 'Partielle', 'Livree', 'Annulee')"),
        schema="public",
    )

    op.create_table(
        "ligne_commande",
        sa.Column("id_ligne", sa.Integer, primary_key=True),
        sa.Column("commande_id", sa.Integer, sa.ForeignKey("public.commande.id_commande"), nullable=False),
        sa.Column("piece_id", sa.Integer, sa.ForeignKey("public.piece.id_piece"), nullable=False),
        sa.Column("description_libre", sa.Text),
        sa.Column("quantite_commandee", sa.Integer, nullable=False),
        sa.Column("prix_unitaire_ht", sa.Numeric(10, 4), nullable=False),
        sa.Column("quantite_recue", sa.Integer, server_default="0"),
        sa.Column("statut_ligne", sa.Enum("Attente", "Partielle", "Complete", "Annulee", name="statut_ligne_commande"), nullable=False, server_default="Attente"),
        sa.CheckConstraint("prix_unitaire_ht >= 0"),
        sa.CheckConstraint("quantite_commandee > 0"),
        schema="public",
    )

    op.create_table(
        "appel_offre",
        sa.Column("id_ao", sa.Integer, primary_key=True),
        sa.Column("commande_id", sa.Integer, sa.ForeignKey("public.commande.id_commande"), nullable=False, unique=True),
        sa.Column("reference_ao", sa.String(50), unique=True, nullable=False),
        sa.Column("titre", sa.String(255)),
        sa.Column("createur_id", sa.Integer, sa.ForeignKey("public.utilisateur.id_utilisateur")),
        sa.Column("date_creation", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("date_cloture_prevue", sa.DateTime(timezone=True)),
        sa.Column("statut", sa.Enum("Ouvert", "Clos", "Annulé", "Archivé", name="statut_ao"), nullable=False, server_default="Ouvert"),
        schema="public",
    )

    op.create_table(
        "ao_fournisseur_consulte",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ao_id", sa.Integer, sa.ForeignKey("public.appel_offre.id_ao"), nullable=False),
        sa.Column("fournisseur_id", sa.Integer, sa.ForeignKey("public.fournisseur.id_fournisseur"), nullable=False),
        sa.Column("date_envoi", sa.DateTime(timezone=True)),
        sa.Column("a_repondu", sa.Boolean, server_default=sa.text("false")),
        sa.UniqueConstraint("ao_id", "fournisseur_id"),
        schema="public",
    )

    op.create_table(
        "offre_recue",
        sa.Column("id_offre", sa.Integer, primary_key=True),
        sa.Column("ao_id", sa.Integer, sa.ForeignKey("public.appel_offre.id_ao"), nullable=False),
        sa.Column("fournisseur_id", sa.Integer, sa.ForeignKey("public.fournisseur.id_fournisseur"), nullable=False),
        sa.Column("date_reception", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reference_offre_fournisseur", sa.String(100)),
        sa.Column("delai_livraison_propose_j", sa.Integer),
        sa.Column("validite_offre_jours", sa.Integer),
        sa.Column("conditions_commerciales", sa.Text),
        schema="public",
    )

    op.create_table(
        "offre_recue_ligne",
        sa.Column("id_offre_ligne", sa.Integer, primary_key=True),
        sa.Column("offre_id", sa.Integer, sa.ForeignKey("public.offre_recue.id_offre"), nullable=False),
        sa.Column("piece_id", sa.Integer, sa.ForeignKey("public.piece.id_piece"), nullable=False),
        sa.Column("prix_unitaire_ht_propose", sa.Numeric(10, 4), nullable=False),
        sa.Column("remise_percent", sa.Numeric(5, 2), server_default="0.00"),
        sa.Column("commentaire", sa.Text),
        schema="public",
    )

    op.create_table(
        "contrat_achat",
        sa.Column("id_contrat_achat", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("reference_interne_contrat", sa.String(50), unique=True, nullable=False),
        sa.Column("objet_contrat", sa.Text, nullable=False),
        sa.Column("fournisseur_id", sa.Integer, sa.ForeignKey("public.fournisseur.id_fournisseur"), nullable=False),
        sa.Column("numero_contrat_fournisseur", sa.String(100)),
        sa.Column("date_signature", sa.Date),
        sa.Column("date_debut_validite", sa.Date, nullable=False),
        sa.Column("date_fin_validite", sa.Date, nullable=False),
        sa.Column("date_prochain_renouvellement", sa.Date),
        sa.Column("montant_total_engage", sa.Numeric(14, 2)),
        sa.Column("devise_contrat", sa.String(3), server_default="EUR"),
        sa.Column("type_contrat", sa.Text),
        sa.Column("statut_contrat", sa.Enum("Brouillon", "Actif", "Expiré", "Renouvelé", "Annulé", "Archivé", name="statut_contrat"), nullable=False, server_default="Actif"),
        sa.Column("contact_principal_achat_id", sa.Integer, sa.ForeignKey("public.utilisateur.id_utilisateur")),
        sa.Column("contact_fournisseur_specifique", sa.Text),
        sa.Column("chemin_document_pdf", sa.Text),
        sa.Column("notes_contrat", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="public",
    )

    op.create_table(
        "prestation_achat",
        sa.Column("id_prestation_achat", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("reference_prestation", sa.String(50), unique=True),
        sa.Column("maintenance_id", sa.Integer),
        sa.Column("description_besoin", sa.Text, nullable=False),
        sa.Column("type_prestation", sa.Enum("SERVICE_MAINTENANCE", "PIECE_HORS_CATALOGUE", "CONSULTATION_EXTERNE", "FORMATION", "SOUS_TRAITANCE_FORFAIT", "FRAIS_DEPLACEMENT", "AUTRE_SERVICE", name="type_prestation"), nullable=False),
        sa.Column("statut_prestation", sa.Enum("DEMANDE_INITIALE", "EN_DEVIS", "OFFRE_ANALYSE", "COMMANDE_A_EMETTRE", "COMMANDE_EMISE", "PRESTATION_EN_COURS", "PRESTATION_TERMINEE", "FACTURE_RECUE", "ATTENTE_REGULARISATION", "REGULARISATION_EMISE", "CLOS", "ANNULEE", name="statut_prestation"), nullable=False, server_default="DEMANDE_INITIALE"),
        sa.Column("urgence", sa.Boolean, server_default=sa.text("false")),
        sa.Column("demandeur_maintenance_id", sa.Integer, sa.ForeignKey("public.utilisateur.id_utilisateur")),
        sa.Column("date_demande", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("acheteur_responsable_id", sa.Integer, sa.ForeignKey("public.utilisateur.id_utilisateur")),
        sa.Column("sous_contrat", sa.Boolean, server_default=sa.text("false")),
        sa.Column("contrat_achat_id", sa.Integer, sa.ForeignKey("public.contrat_achat.id_contrat_achat")),
        sa.Column("reference_contrat_fournisseur", sa.Text),
        sa.Column("fournisseur_id", sa.Integer, sa.ForeignKey("public.fournisseur.id_fournisseur")),
        sa.Column("contact_fournisseur_prestation", sa.Text),
        sa.Column("montant_estime_demande", sa.Numeric(12, 2)),
        sa.Column("devise_estimation", sa.String(3), server_default="EUR"),
        sa.Column("commande_initiale_id", sa.Integer, sa.ForeignKey("public.commande.id_commande")),
        sa.Column("description_travaux_reels", sa.Text),
        sa.Column("montant_facture_final", sa.Numeric(12, 2)),
        sa.Column("devise_facture", sa.String(3)),
        sa.Column("reference_facture_fournisseur", sa.Text),
        sa.Column("date_reception_facture", sa.Date),
        sa.Column("notes_facturation", sa.Text),
        sa.Column("necessite_regularisation", sa.Boolean, server_default=sa.text("false")),
        sa.Column("commande_regularisation_id", sa.Integer, sa.ForeignKey("public.commande.id_commande")),
        sa.Column("montant_regularisation_calcule", sa.Numeric(12, 2)),
        sa.Column("notes_generales", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="public",
    )


def downgrade() -> None:
    op.drop_table("prestation_achat", schema="public")
    op.drop_table("contrat_achat", schema="public")
    op.drop_table("offre_recue_ligne", schema="public")
    op.drop_table("offre_recue", schema="public")
    op.drop_table("ao_fournisseur_consulte", schema="public")
    op.drop_table("appel_offre", schema="public")
    op.drop_table("ligne_commande", schema="public")
    op.drop_table("commande", schema="public")
    op.drop_table("piece_fournisseur_info", schema="public")
    op.drop_table("piece_extension", schema="public")
    op.drop_table("piece", schema="public")
    op.drop_table("utilisateur", schema="public")
    op.drop_table("machine", schema="public")
    op.drop_table("fournisseur", schema="public")
