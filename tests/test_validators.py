"""Unit tests for Pydantic validators."""

import pytest
from datetime import date, datetime
from decimal import Decimal

from app.validators.order_validators import (
    CommandeCreate,
    CommandeUpdate,
    LigneCommandeCreate,
    AppelOffreCreate,
    OffreRecueCreate,
    OffreRecueLigneCreate,
    FournisseurCreate,
    StatutCommande,
    StatutLigneCommande,
    StatutAO,
)


class TestCommandeCreate:
    """Validation tests for CommandeCreate."""

    def test_valid_minimal(self):
        cmd = CommandeCreate(fournisseur_id=1, createur_id=2)
        assert cmd.fournisseur_id == 1
        assert cmd.createur_id == 2
        assert cmd.statut == StatutCommande.BROUILLON
        assert cmd.total_ht == Decimal("0")

    def test_invalid_fournisseur_id(self):
        with pytest.raises(ValueError):
            CommandeCreate(fournisseur_id=0, createur_id=1)

    def test_invalid_createur_id(self):
        with pytest.raises(ValueError):
            CommandeCreate(fournisseur_id=1, createur_id=-5)

    def test_valid_full(self):
        cmd = CommandeCreate(
            fournisseur_id=42,
            createur_id=7,
            date_commande=date(2026, 7, 1),
            date_livraison_prevue=date(2026, 7, 15),
            statut=StatutCommande.VALIDEE,
            total_ht=Decimal("1500.50"),
        )
        assert cmd.total_ht == Decimal("1500.50")
        assert cmd.statut == StatutCommande.VALIDEE


class TestLigneCommandeCreate:
    """Validation tests for LigneCommandeCreate."""

    def test_valid(self):
        lc = LigneCommandeCreate(
            piece_id=1, quantite_commandee=5, prix_unitaire_ht=Decimal("19.99")
        )
        assert lc.piece_id == 1
        assert lc.quantite_commandee == 5
        assert lc.prix_unitaire_ht == Decimal("19.99")

    def test_negative_price(self):
        with pytest.raises(ValueError):
            LigneCommandeCreate(piece_id=1, quantite_commandee=5, prix_unitaire_ht=Decimal("-1"))

    def test_zero_quantity(self):
        with pytest.raises(ValueError):
            LigneCommandeCreate(piece_id=1, quantite_commandee=0, prix_unitaire_ht=Decimal("10"))


class TestAppelOffreCreate:
    """Validation tests for AppelOffreCreate."""

    def test_valid(self):
        ao = AppelOffreCreate(commande_id=1, reference_ao="AO-2026-0001")
        assert ao.statut == StatutAO.OUVERT

    def test_empty_reference(self):
        with pytest.raises(ValueError):
            AppelOffreCreate(commande_id=1, reference_ao="")


class TestFournisseurCreate:
    """Validation tests for FournisseurCreate."""

    def test_valid(self):
        f = FournisseurCreate(nom="ACME Corp", email="contact@acme.com")
        assert f.nom == "ACME Corp"

    def test_invalid_email(self):
        with pytest.raises(ValueError):
            FournisseurCreate(nom="BadCorp", email="not-an-email")
