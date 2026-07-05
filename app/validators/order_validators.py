"""Pydantic validators for purchase order, RFQ, and offer data.

These validators ensure data integrity before database operations.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ── Enums ──

class StatutCommande(str, Enum):
    BROUILLON = "Brouillon"
    VALIDEE = "Validee"
    ENVOYEE = "Envoyee"
    PARTIELLE = "Partielle"
    LIVREE = "Livree"
    ANNULEE = "Annulee"


class StatutLigneCommande(str, Enum):
    ATTENTE = "Attente"
    PARTIELLE = "Partielle"
    COMPLETE = "Complete"
    ANNULEE = "Annulee"


class StatutAO(str, Enum):
    OUVERT = "Ouvert"
    CLOS = "Clos"
    ANNULE = "Annulé"
    ARCHIVE = "Archivé"


class StatutContrat(str, Enum):
    BROUILLON = "Brouillon"
    ACTIF = "Actif"
    EXPIRE = "Expiré"
    RENOUVELE = "Renouvelé"
    ANNULE = "Annulé"
    ARCHIVE = "Archivé"


# ── Commande ──

class CommandeCreate(BaseModel):
    """Validator for creating a new purchase order."""
    fournisseur_id: int = Field(ge=1, description="Supplier ID")
    createur_id: int = Field(ge=1, description="Creator user ID")
    date_commande: date = Field(default_factory=date.today)
    date_livraison_prevue: Optional[date] = None
    statut: StatutCommande = Field(default=StatutCommande.BROUILLON)
    total_ht: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)

    @field_validator("date_livraison_prevue")
    @classmethod
    def delivery_after_order(cls, v, info):
        if v and "date_commande" in info.data:
            if v < info.data["date_commande"]:
                raise ValueError("Delivery date must be on or after order date")
        return v


class LigneCommandeCreate(BaseModel):
    """Validator for adding a line item to an order."""
    piece_id: int = Field(ge=1)
    quantite_commandee: int = Field(ge=1, description="Quantity ordered (>= 1)")
    prix_unitaire_ht: Decimal = Field(ge=0, max_digits=10, decimal_places=4)
    quantite_recue: int = Field(default=0, ge=0)
    statut_ligne: StatutLigneCommande = Field(default=StatutLigneCommande.ATTENTE)


class CommandeUpdate(BaseModel):
    """Validator for updating an existing order."""
    statut: Optional[StatutCommande] = None
    total_ht: Optional[Decimal] = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    date_livraison_prevue: Optional[date] = None


class AppelOffreCreate(BaseModel):
    """Validator for creating a new RFQ."""
    commande_id: int = Field(ge=1)
    reference_ao: str = Field(min_length=1, max_length=50)
    titre: Optional[str] = Field(default=None, max_length=255)
    createur_id: Optional[int] = Field(default=None, ge=1)
    date_cloture_prevue: Optional[datetime] = None
    statut: StatutAO = Field(default=StatutAO.OUVERT)


class OffreRecueCreate(BaseModel):
    """Validator for recording a received supplier offer."""
    ao_id: int = Field(ge=1)
    fournisseur_id: int = Field(ge=1)
    reference_offre_fournisseur: Optional[str] = Field(default=None, max_length=100)
    delai_livraison_propose_j: Optional[int] = Field(default=None, ge=0)
    validite_offre_jours: Optional[int] = Field(default=None, ge=1)
    conditions_commerciales: Optional[str] = None


class OffreRecueLigneCreate(BaseModel):
    """Validator for a line item in a supplier offer."""
    piece_id: int = Field(ge=1)
    prix_unitaire_ht_propose: Decimal = Field(ge=0, max_digits=10, decimal_places=4)
    remise_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100, max_digits=5, decimal_places=2)
    commentaire: Optional[str] = None


class FournisseurCreate(BaseModel):
    """Validator for creating a new supplier."""
    nom: str = Field(min_length=1, max_length=100)
    email: Optional[str] = Field(default=None, max_length=100)
    adresse: Optional[str] = None
    telephone: Optional[str] = Field(default=None, max_length=50)
    devise: str = Field(default="EUR", min_length=3, max_length=10)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v and "@" not in v:
            raise ValueError("Invalid email format")
        return v
