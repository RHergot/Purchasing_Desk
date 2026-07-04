# Fichier: app/models/purchase_models.py (Adapté pour le schéma 'public')

# Fichier: app/models/purchase_models.py
# Cette version modélise les tables existantes 'commande' et 'ligne_commande'
# et prépare les futures tables pour les appels d'offres.
import datetime
from sqlalchemy import (Column, Integer, String, Numeric, DateTime, ForeignKey,
                        Enum, Text, Float, CheckConstraint, Boolean, Date)
from sqlalchemy.orm import relationship
# Imports corrects
from database import Base, get_db_session
from app.models.shared_models import Article # Article est notre 'piece'
from app.models.shared_models import Utilisateur

# On définit les ENUMs basés sur vos contraintes CHECK pour plus de robustesse
STATUT_COMMANDE = Enum('Brouillon', 'Validee', 'Envoyee', 'Partielle', 'Livree', 'Annulee', name='statut_commande')
STATUT_LIGNE_COMMANDE = Enum('Attente', 'Partielle', 'Complete', 'Annulee', name='statut_ligne_commande')
STATUT_CONTRAT_PYTHON = Enum(
    'Brouillon', 'Actif', 'Expiré', 'Renouvelé', 'Annulé', 'Archivé',
    name='statut_contrat_python_enum' # Nom unique pour l'enum Python
)
TYPE_PRESTATION_PYTHON = Enum(
    'SERVICE_MAINTENANCE', 'PIECE_HORS_CATALOGUE', 'CONSULTATION_EXTERNE', 
    'FORMATION', 'SOUS_TRAITANCE_FORFAIT', 'FRAIS_DEPLACEMENT', 'AUTRE_SERVICE',
    name='type_prestation_python_enum',
    # Si les types ENUM SQL existent déjà, on peut les utiliser avec create_type=False
    # mais il faut s'assurer que les noms correspondent.
    # Sinon, SQLAlchemy essaiera de les créer.
    # Pour la portabilité et la simplicité, on peut juste utiliser String et valider en Python,
    # ou utiliser les ENUM Python et les laisser créer les types en BDD s'ils n'existent pas.
)

STATUT_PRESTATION_PYTHON = Enum(
    'DEMANDE_INITIALE', 'EN_DEVIS', 'OFFRE_ANALYSE', 'COMMANDE_A_EMETTRE',
    'COMMANDE_EMISE', 'PRESTATION_EN_COURS', 'PRESTATION_TERMINEE', 
    'FACTURE_RECUE', 'ATTENTE_REGULARISATION', 'REGULARISATION_EMISE',
    'CLOS', 'ANNULEE',
    name='statut_prestation_python_enum'
)

class ContratAchat(Base):
    __tablename__ = 'contrat_achat'
    __table_args__ = {'schema': 'public'}

    id_contrat_achat = Column(Integer, primary_key=True, autoincrement=True)
    reference_interne_contrat = Column(String(50), unique=True, nullable=False)
    objet_contrat = Column(Text, nullable=False)
    fournisseur_id = Column(Integer, ForeignKey('public.fournisseur.id_fournisseur'), nullable=False)
    
    numero_contrat_fournisseur = Column(String(100))
    
    date_signature = Column(Date)
    date_debut_validite = Column(Date, nullable=False)
    date_fin_validite = Column(Date, nullable=False)
    date_prochain_renouvellement = Column(Date)
    
    montant_total_engage = Column(Numeric(14,2))
    devise_contrat = Column(String(3), default='EUR')
    
    type_contrat = Column(Text)
    statut_contrat = Column(STATUT_CONTRAT_PYTHON, nullable=False, default='Actif')
    
    contact_principal_achat_id = Column(Integer, ForeignKey('public.utilisateur.id_utilisateur'))
    contact_fournisseur_specifique = Column(Text)
    
    chemin_document_pdf = Column(Text)
    notes_contrat = Column(Text)
    
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now, onupdate=datetime.datetime.now)

    # Relations
    fournisseur = relationship("Fournisseur", lazy="joined")
    acheteur_responsable_contrat = relationship("Utilisateur", foreign_keys=[contact_principal_achat_id], lazy="joined")

    # Relation inverse vers PrestationAchat (si une prestation est liée à CE contrat)
    prestations_liees = relationship("PrestationAchat", back_populates="contrat_details")

    def __repr__(self):
        return f"<ContratAchat(id={self.id_contrat_achat}, ref='{self.reference_interne_contrat}', fournisseur='{self.fournisseur.nom if self.fournisseur else ''}')>"

class PrestationAchat(Base):
    __tablename__ = 'prestation_achat'
    __table_args__ = {'schema': 'public'}

    id_prestation_achat = Column(Integer, primary_key=True, autoincrement=True)
    reference_prestation = Column(String(50), unique=True)
    
    maintenance_id = Column(Integer, ForeignKey('public.maintenance.id_maintenance')) # Supposant que la table GMAO s'appelle 'maintenance'
    description_besoin = Column(Text, nullable=False)
    type_prestation = Column(TYPE_PRESTATION_PYTHON, nullable=False) # Utilise l'ENUM Python
    statut_prestation = Column(STATUT_PRESTATION_PYTHON, nullable=False, default='DEMANDE_INITIALE')
    urgence = Column(Boolean, default=False)
    demandeur_maintenance_id = Column(Integer, ForeignKey('public.utilisateur.id_utilisateur'))
    date_demande = Column(DateTime(timezone=True), default=datetime.datetime.now)
    acheteur_responsable_id = Column(Integer, ForeignKey('public.utilisateur.id_utilisateur'))

    sous_contrat = Column(Boolean, default=False)
    contrat_achat_id = Column(Integer, ForeignKey('public.contrat_achat.id_contrat_achat'))
    contrat_details = relationship("ContratAchat", back_populates="prestations_liees", foreign_keys=[contrat_achat_id], lazy="joined")
    reference_contrat_fournisseur = Column(Text)

    fournisseur_id = Column(Integer, ForeignKey('public.fournisseur.id_fournisseur'))
    contact_fournisseur_prestation = Column(Text)

    montant_estime_demande = Column(Numeric(12,2))
    devise_estimation = Column(String(3), default='EUR') # CHAR(3) devient String(3)
    commande_initiale_id = Column(Integer, ForeignKey('public.commande.id_commande'))
    
    description_travaux_reels = Column(Text)
    montant_facture_final = Column(Numeric(12,2))
    devise_facture = Column(String(3))
    reference_facture_fournisseur = Column(Text)
    date_reception_facture = Column(Date) # Utiliser Date de SQLAlchemy
    notes_facturation = Column(Text)

    necessite_regularisation = Column(Boolean, default=False)
    commande_regularisation_id = Column(Integer, ForeignKey('public.commande.id_commande'))
    montant_regularisation_calcule = Column(Numeric(12,2))

    notes_generales = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now, onupdate=datetime.datetime.now)

    # Relations
    # Si la table GMAO 'maintenance' a un modèle SQLAlchemy (ex: MaintenanceGmao)
    # maintenance_gmao = relationship("MaintenanceGmao", foreign_keys=[maintenance_id])
    demandeur_maintenance = relationship("Utilisateur", foreign_keys=[demandeur_maintenance_id], lazy="joined")
    acheteur_responsable = relationship("Utilisateur", foreign_keys=[acheteur_responsable_id], lazy="joined")
    fournisseur = relationship("Fournisseur", foreign_keys=[fournisseur_id], lazy="joined")
    commande_initiale = relationship("Commande", foreign_keys=[commande_initiale_id], primaryjoin="PrestationAchat.commande_initiale_id == Commande.id_commande", lazy="joined")
    commande_regularisation = relationship("Commande", foreign_keys=[commande_regularisation_id], primaryjoin="PrestationAchat.commande_regularisation_id == Commande.id_commande", lazy="joined")

    def __repr__(self):
        return f"<PrestationAchat(id={self.id_prestation_achat}, ref='{self.reference_prestation}', statut='{self.statut_prestation}')>"

class Commande(Base):
    __tablename__ = 'commande'
    id_commande = Column(Integer, primary_key=True)
    numero_commande = Column(Text)
    fournisseur_id = Column(Integer, ForeignKey('public.fournisseur.id_fournisseur'), nullable=False)
    createur_id = Column(Integer, ForeignKey('public.utilisateur.id_utilisateur'), nullable=False)
    
    # Note: Les champs de date sont des TEXT. On les gardera comme String pour le moment.
    date_commande = Column(DateTime, nullable=False)
    date_livraison_prevue = Column(DateTime)
    
    statut = Column(STATUT_COMMANDE, nullable=False, default='Brouillon')
    total_ht = Column(Numeric(10, 2), default=0.0)
    
    # Relations
    fournisseur = relationship("Fournisseur")
    createur = relationship("Utilisateur")
    lignes = relationship("LigneCommande", back_populates="commande", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint(statut.in_(['Brouillon', 'Validee', 'Envoyee', 'Partielle', 'Livree', 'Annulee'])),
        {'schema': 'public'}
    )

    def __repr__(self):
        return f"<Commande(id={self.id_commande}, numero='{self.numero_commande}', statut='{self.statut}')>"


class LigneCommande(Base):
    __tablename__ = 'ligne_commande'
    id_ligne = Column(Integer, primary_key=True)
    commande_id = Column(Integer, ForeignKey('public.commande.id_commande'), nullable=False)
    piece_id = Column(Integer, ForeignKey('public.piece.id_piece'), nullable=False)
    description_libre = Column(Text)
    quantite_commandee = Column(Integer, nullable=False)
    prix_unitaire_ht = Column(Numeric(10, 4), nullable=False)
    quantite_recue = Column(Integer, default=0)
    statut_ligne = Column(STATUT_LIGNE_COMMANDE, nullable=False, default='Attente')

    # Relations
    commande = relationship("Commande", back_populates="lignes")
    piece = relationship("Article")
    
    __table_args__ = (
        CheckConstraint('prix_unitaire_ht >= 0'),
        CheckConstraint('quantite_commandee > 0'),
        {'schema': 'public'}
    )

# ... (garder les imports et les classes Commande et LigneCommande existantes) ...

# =========================================================================
# Nouveaux Modèles pour le Processus d'Appel d'Offres (Phase 2)
# =========================================================================

STATUT_AO = Enum('Ouvert', 'Clos', 'Annulé', 'Archivé', name='statut_ao')

class AppelOffre(Base):
    __tablename__ = 'appel_offre'
    id_ao = Column(Integer, primary_key=True)
    commande_id = Column(Integer, ForeignKey('public.commande.id_commande'), nullable=False, unique=True)
    reference_ao = Column(String(50), unique=True, nullable=False)
    titre = Column(String(255))
    createur_id = Column(Integer, ForeignKey('public.utilisateur.id_utilisateur'))
    date_creation = Column(DateTime(timezone=True), default=datetime.datetime.now)
    date_cloture_prevue = Column(DateTime(timezone=True))
    statut = Column(STATUT_AO, nullable=False, default='Ouvert')
    __table_args__ = {'schema': 'public'}

    # Relations
    commande = relationship("Commande")
    createur = relationship("Utilisateur")
    fournisseurs_consultes = relationship("AoFournisseurConsulte", back_populates="appel_offre", cascade="all, delete-orphan")
    offres_recues = relationship("OffreRecue", back_populates="appel_offre", cascade="all, delete-orphan")

class AoFournisseurConsulte(Base):
    __tablename__ = 'ao_fournisseur_consulte'
    id = Column(Integer, primary_key=True)
    ao_id = Column(Integer, ForeignKey('public.appel_offre.id_ao'), nullable=False)
    fournisseur_id = Column(Integer, ForeignKey('public.fournisseur.id_fournisseur'), nullable=False)
    date_envoi = Column(DateTime(timezone=True))
    a_repondu = Column(Boolean, default=False)
    __table_args__ = {'schema': 'public'}
    
    # Relations
    appel_offre = relationship("AppelOffre", back_populates="fournisseurs_consultes")
    fournisseur = relationship("Fournisseur")

class OffreRecue(Base):
    __tablename__ = 'offre_recue'
    id_offre = Column(Integer, primary_key=True)
    ao_id = Column(Integer, ForeignKey('public.appel_offre.id_ao'), nullable=False)
    fournisseur_id = Column(Integer, ForeignKey('public.fournisseur.id_fournisseur'), nullable=False)
    date_reception = Column(DateTime(timezone=True), default=datetime.datetime.now)
    reference_offre_fournisseur = Column(String(100))
    delai_livraison_propose_j = Column(Integer)
    validite_offre_jours = Column(Integer)
    conditions_commerciales = Column(Text)
    __table_args__ = {'schema': 'public'}
    
    # Relations
    appel_offre = relationship("AppelOffre", back_populates="offres_recues")
    fournisseur = relationship("Fournisseur")
    lignes_offre = relationship("OffreRecueLigne", back_populates="offre_recue", cascade="all, delete-orphan")
    
class OffreRecueLigne(Base):
    __tablename__ = 'offre_recue_ligne'
    id_offre_ligne = Column(Integer, primary_key=True)
    offre_id = Column(Integer, ForeignKey('public.offre_recue.id_offre'), nullable=False)
    piece_id = Column(Integer, ForeignKey('public.piece.id_piece'), nullable=False)
    prix_unitaire_ht_propose = Column(Numeric(10, 4), nullable=False)
    remise_percent = Column(Numeric(5, 2), default=0.00)
    commentaire = Column(Text)
    __table_args__ = {'schema': 'public'}

    # Relations
    offre_recue = relationship("OffreRecue", back_populates="lignes_offre")
    piece = relationship("Article")