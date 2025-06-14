# Fichier: app/models/shared_models.py (Adapté pour le schéma 'public')

import datetime
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Boolean, Date, Text, UniqueConstraint, DateTime
# from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
# Imports corrects
from app.database import Base

class Utilisateur(Base):
    __tablename__ = 'utilisateur'
    id_utilisateur = Column(Integer, primary_key=True)
    nom_complet = Column(String(100))
    role = Column(String(50))
    email = Column(String(100), unique=True)
    login = Column(String(50), unique=True)
    __table_args__ = {'schema': 'public'} # <--- AJOUT IMPORTANT

    def __repr__(self):
        return f"<Utilisateur(id={self.id_utilisateur}, nom='{self.nom_complet}')>"

class Fournisseur(Base):
    __tablename__ = 'fournisseur'
    id_fournisseur = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    email = Column(String(100))
    adresse = Column(String) # Ajout basé sur le dump SQL (pour le template)
    telephone = Column(String(50)) # Ajout basé sur le dump SQL (pour le template)
    devise = Column(String(10))  # <--- AJOUT IMPORTANT DU CHAMP DEVISE
    __table_args__ = {'schema': 'public'}

    def __repr__(self):
        return f"<Fournisseur(id={self.id_fournisseur}, nom='{self.nom}')>"

class Article(Base):
    __tablename__ = 'piece'
    id_piece = Column(Integer, primary_key=True)
    reference = Column(String(50), unique=True, nullable=False)
    designation = Column('nom', String(255))
    fournisseur_id_default = Column('fournisseur_pref_id', Integer, ForeignKey('public.fournisseur.id_fournisseur')) # Préciser le schéma dans la FK
    prix_achat_ht = Column('prix_unitaire', Numeric(10, 2))
    __table_args__ = {'schema': 'public'} # <--- AJOUT IMPORTANT

    fournisseur_default = relationship("Fournisseur")

    def __repr__(self):
        return f"<Article(id={self.id_piece}, reference='{self.reference}')>"


# --- NOUVELLE CLASSE ---
class PieceFournisseurInfo(Base):
    __tablename__ = 'piece_fournisseur_info'
    id_piece_fournisseur_info = Column(Integer, primary_key=True, autoincrement=True)
    piece_id = Column(Integer, ForeignKey('public.piece.id_piece'), nullable=False)
    fournisseur_id = Column(Integer, ForeignKey('public.fournisseur.id_fournisseur'), nullable=False)
    
    reference_fournisseur = Column(String(100))
    prix_catalogue_fournisseur = Column(Numeric(12, 4))
    devise_prix_catalogue = Column(String(10), default='EUR')
    delai_livraison_standard_j = Column(Integer)
    unite_achat_fournisseur = Column(String(50))
    quantite_min_commande = Column(Integer)
    dernier_prix_negocie = Column(Numeric(12, 4))
    date_dernier_prix_negocie = Column(Date)
    commentaire = Column(Text) # Text est plus approprié que String pour les commentaires longs
    actif = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Relation pour accéder facilement à la pièce et au fournisseur depuis cette table
    piece = relationship("Article", backref="info_fournisseurs") # 'Article' est le nom de notre classe pour 'piece'
    fournisseur = relationship("Fournisseur", backref="info_pieces")
    
    __table_args__ = (
        UniqueConstraint('piece_id', 'fournisseur_id', name='uq_piece_fournisseur'),
        {'schema': 'public'}
    )

    def __repr__(self):
        return f"<PieceFournisseurInfo(piece_id={self.piece_id}, fournisseur_id={self.fournisseur_id}, ref='{self.reference_fournisseur}')>"