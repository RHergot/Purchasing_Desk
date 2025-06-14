# Fichier: app/models/purchase_models.py (Adapté pour le schéma 'public')

# Fichier: app/models/purchase_models.py
# Cette version modélise les tables existantes 'commande' et 'ligne_commande'
# et prépare les futures tables pour les appels d'offres.
import datetime
from sqlalchemy import (Column, Integer, String, Numeric, DateTime, ForeignKey,
                        Enum, Text, Float, CheckConstraint, Boolean)
from sqlalchemy.orm import relationship
# Imports corrects
from app.database import Base
from .shared_models import Article, Utilisateur, Fournisseur # Le '.' est un import relatif correct

# On définit les ENUMs basés sur vos contraintes CHECK pour plus de robustesse
STATUT_COMMANDE = Enum('Brouillon', 'Validee', 'Envoyee', 'Partielle', 'Livree', 'Annulee', name='statut_commande')
STATUT_LIGNE_COMMANDE = Enum('Attente', 'Partielle', 'Complete', 'Annulee', name='statut_ligne_commande')

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