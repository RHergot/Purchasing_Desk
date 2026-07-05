"""Unit tests for SQLAlchemy model definitions.

These tests verify model metadata (table names, columns, constraints)
without requiring a database connection.
"""

import pytest
from sqlalchemy import inspect


# ── Helper ──

def get_column_names(model):
    """Return column names for a SQLAlchemy model."""
    return {c.name for c in inspect(model).columns}


def get_required_columns(model):
    """Return column names marked as nullable=False."""
    return {c.name for c in inspect(model).columns if not c.nullable}


# ── Shared Models ──

class TestFournisseur:
    """Tests for the Fournisseur model."""

    def test_table_name(self):
        from app.models.shared_models import Fournisseur
        assert Fournisseur.__tablename__ == "fournisseur"

    def test_schema(self):
        from app.models.shared_models import Fournisseur
        assert Fournisseur.__table_args__ == {"schema": "public"}

    def test_nom_not_null(self):
        from app.models.shared_models import Fournisseur
        cols = get_required_columns(Fournisseur)
        assert "nom" in cols

    def test_columns_exist(self):
        from app.models.shared_models import Fournisseur
        cols = get_column_names(Fournisseur)
        expected = {"id_fournisseur", "nom", "email", "adresse", "telephone", "devise"}
        assert expected.issubset(cols)


class TestArticle:
    """Tests for the Article (piece) model."""

    def test_table_name(self):
        from app.models.shared_models import Article
        assert Article.__tablename__ == "piece"

    def test_reference_not_null(self):
        from app.models.shared_models import Article
        cols = get_required_columns(Article)
        assert "reference" in cols

    def test_column_mappings(self):
        from app.models.shared_models import Article
        cols = get_column_names(Article)
        expected = {"id_piece", "reference", "statut", "categorie",
                     "stock_actuel", "stock_alerte", "unite",
                     "fournisseur_pref_id"}
        assert expected.issubset(cols)


class TestUtilisateur:
    """Tests for the Utilisateur model."""

    def test_table_name(self):
        from app.models.shared_models import Utilisateur
        assert Utilisateur.__tablename__ == "utilisateur"

    def test_login_unique(self):
        from app.models.shared_models import Utilisateur
        login_col = getattr(Utilisateur, "login")
        assert login_col.unique is True


# ── Purchase Models ──

class TestCommande:
    """Tests for the Commande model."""

    def test_table_name(self):
        from app.models.purchase_models import Commande
        assert Commande.__tablename__ == "commande"

    def test_required_columns(self):
        from app.models.purchase_models import Commande
        cols = get_required_columns(Commande)
        assert "fournisseur_id" in cols
        assert "createur_id" in cols
        assert "date_commande" in cols

    def test_foreign_keys(self):
        from app.models.purchase_models import Commande
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(Commande)
        table = mapper.tables[0]  # SQLAlchemy 2.x Mapper API
        fks = {fk.parent.name for fk in table.foreign_keys}
        assert "fournisseur_id" in fks
        assert "createur_id" in fks

    def test_statut_default(self):
        from app.models.purchase_models import Commande
        statut_col = getattr(Commande, "statut")
        assert statut_col.default.arg == "Brouillon"


class TestLigneCommande:
    """Tests for the LigneCommande model."""

    def test_table_name(self):
        from app.models.purchase_models import LigneCommande
        assert LigneCommande.__tablename__ == "ligne_commande"

    def test_required_columns(self):
        from app.models.purchase_models import LigneCommande
        cols = get_required_columns(LigneCommande)
        assert "commande_id" in cols
        assert "piece_id" in cols
        assert "quantite_commandee" in cols
        assert "prix_unitaire_ht" in cols

    def test_check_constraints(self):
        from app.models.purchase_models import LigneCommande
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(LigneCommande)
        table = mapper.tables[0]
        checks = [c.sqltext.text for c in table.constraints
                  if hasattr(c, "sqltext")]
        assert any("prix_unitaire_ht >= 0" in chk for chk in checks)
        assert any("quantite_commandee > 0" in chk for chk in checks)


class TestAppelOffre:
    """Tests for the AppelOffre model."""

    def test_table_name(self):
        from app.models.purchase_models import AppelOffre
        assert AppelOffre.__tablename__ == "appel_offre"

    def test_unique_commande_id(self):
        from app.models.purchase_models import AppelOffre
        col = getattr(AppelOffre, "commande_id")
        assert col.unique is True

    def test_unique_reference(self):
        from app.models.purchase_models import AppelOffre
        col = getattr(AppelOffre, "reference_ao")
        assert col.unique is True


class TestOffreRecue:
    """Tests for the OffreRecue model."""

    def test_table_name(self):
        from app.models.purchase_models import OffreRecue
        assert OffreRecue.__tablename__ == "offre_recue"

    def test_required_columns(self):
        from app.models.purchase_models import OffreRecue
        cols = get_required_columns(OffreRecue)
        assert "ao_id" in cols
        assert "fournisseur_id" in cols


class TestContratAchat:
    """Tests for the ContratAchat model."""

    def test_table_name(self):
        from app.models.purchase_models import ContratAchat
        assert ContratAchat.__tablename__ == "contrat_achat"

    def test_unique_reference(self):
        from app.models.purchase_models import ContratAchat
        col = getattr(ContratAchat, "reference_interne_contrat")
        assert col.unique is True


class TestPieceFournisseurInfo:
    """Tests for the PieceFournisseurInfo model."""

    def test_table_name(self):
        from app.models.shared_models import PieceFournisseurInfo
        assert PieceFournisseurInfo.__tablename__ == "piece_fournisseur_info"

    def test_unique_constraint(self):
        from app.models.shared_models import PieceFournisseurInfo
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(PieceFournisseurInfo)
        table = mapper.tables[0]
        # Should have a UniqueConstraint in table_args or on the Table itself
        from sqlalchemy import UniqueConstraint
        has_table_unique = any(
            isinstance(c, UniqueConstraint)
            for c in table.constraints
        )
        name_match = "uq_piece_fournisseur"
        has_named = name_match in [c.name for c in table.constraints if c.name]
        assert has_table_unique or has_named, \
            f"PieceFournisseurInfo should have a unique constraint (constraints: {[c.name for c in table.constraints]})"
