import datetime
from sqlalchemy import (Column, Integer, String, Numeric, ForeignKey, 
                        Boolean, Date, Text, UniqueConstraint, DateTime)
from sqlalchemy.orm import relationship
from database import Base # S'assurer que Base est importé depuis notre module database

class Fournisseur(Base):
    __tablename__ = 'fournisseur'
    __table_args__ = {'schema': 'public'}

    id_fournisseur = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    email = Column(String(100))
    adresse = Column(Text) # Changé de String à Text pour les adresses longues
    telephone = Column(String(50))
    devise = Column(String(10), default='EUR')
    # Ajoutez d'autres champs de la table fournisseur si nécessaire pour l'application

    # Relation inverse depuis PieceFournisseurInfo (si vous voulez naviguer de Fournisseur vers ses infos pièces)
    # info_pieces = relationship("PieceFournisseurInfo", back_populates="fournisseur")

    def __repr__(self):
        return f"<Fournisseur(id={self.id_fournisseur}, nom='{self.nom}')>"

class Machine(Base):
    __tablename__ = 'machine'
    __table_args__ = {'schema': 'public'}

    id_machine = Column(Integer, primary_key=True)
    nom = Column(String(100))
    # Ajoutez d'autres champs de la table machine si nécessaire

    # Relation inverse depuis PieceExtension (si vous voulez naviguer de Machine vers ses PieceExtensions)
    # pieces_extensions = relationship("PieceExtension", back_populates="machine")

    def __repr__(self):
        return f"<Machine(id={self.id_machine}, nom='{self.nom}')>"

class Utilisateur(Base):
    __tablename__ = 'utilisateur'
    __table_args__ = {'schema': 'public'}

    id_utilisateur = Column(Integer, primary_key=True)
    nom_complet = Column(String(100))
    role = Column(String(50))
    email = Column(String(100), unique=True) # Assurez-vous que c'est nullable=False si requis par la BDD
    login = Column(String(50), unique=True) # Assurez-vous que c'est nullable=False si requis par la BDD

    def __repr__(self):
        return f"<Utilisateur(id={self.id_utilisateur}, nom='{self.nom_complet}')>"

class Article(Base): # Notre classe pour la table 'piece'
    __tablename__ = 'piece'
    __table_args__ = {'schema': 'public'}

    id_piece = Column(Integer, primary_key=True)
    reference = Column(String(50), unique=True, nullable=False)
    designation = Column('nom', String(255))
    fournisseur_id_default = Column('fournisseur_pref_id', Integer, ForeignKey('public.fournisseur.id_fournisseur'))
    prix_achat_ht = Column('prix_unitaire', Numeric(10, 2)) # Le prix de référence interne
    
    statut = Column(String(50), default='actif') # Nom de colonne 'statut' implicite
    categorie = Column(String(100))             # Nom de colonne 'categorie' implicite
    stock_actuel = Column(Integer, default=0)    # Nom de colonne 'stock_actuel' implicite
    stock_alerte = Column(Integer, default=0)    # Nom de colonne 'stock_alerte' implicite
    unite = Column(String(50))                   # Nom de colonne 'unite' implicite
    
    # Champs optionnels de votre dump SQL que vous pourriez vouloir ajouter au modèle :
    # stock_reserve = Column(Integer, default=0)
    # emplacement_stockage = Column(String(100))
    # updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now, onupdate=datetime.datetime.now)

    # Relations
    fournisseur_default = relationship("Fournisseur") # Basé sur fournisseur_id_default
    
    # Relation vers PieceExtension (1-à-0 ou 1-à-1)
    # Le nom 'extension_info' sera utilisé dans PieceExtension pour back_populates
    extension_info = relationship("PieceExtension", uselist=False, back_populates="piece", cascade="all, delete-orphan")
    
    # Relation vers PieceFournisseurInfo (1-à-Plusieurs)
    # Le nom 'info_fournisseurs' sera utilisé dans PieceFournisseurInfo pour back_populates
    info_fournisseurs = relationship("PieceFournisseurInfo", back_populates="piece", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Article(id={self.id_piece}, ref='{self.reference}', nom='{self.designation}', statut='{self.statut}')>"

class PieceExtension(Base):
    __tablename__ = 'piece_extension'
    __table_args__ = {'schema': 'public'}

    # 'id_piece' est la clé primaire de cette table ET la clé étrangère vers la table 'piece'
    id_piece = Column(Integer, ForeignKey('public.piece.id_piece'), primary_key=True)
    
    # Les autres colonnes de votre table piece_extension
    unite_id = Column(Integer) # Ajoutez ForeignKey si ce sont des FK vers d'autres tables
    categorie_id = Column(Integer) # Ajoutez ForeignKey
    emplacement_id = Column(Integer) # Ajoutez ForeignKey
    statut_id = Column(Integer) # Ajoutez ForeignKey
    machine_id = Column(Integer, ForeignKey('public.machine.id_machine'))

    # Relations
    piece = relationship("Article", back_populates="extension_info") 
    machine = relationship("Machine")
    # Ajoutez des relations pour unite, categorie, emplacement, statut si ce sont des tables séparées

    def __repr__(self):
        return f"<PieceExtension(id_piece={self.id_piece}, machine_id={self.machine_id})>"


class PieceFournisseurInfo(Base):
    __tablename__ = 'piece_fournisseur_info'
    __table_args__ = (
        UniqueConstraint('piece_id', 'fournisseur_id', name='uq_piece_fournisseur'),
        {'schema': 'public'}
    )

    id_piece_fournisseur_info = Column(Integer, primary_key=True, autoincrement=True)
    # Clé étrangère vers piece - Assurez-vous que le nom de la colonne est correct
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
    commentaire = Column(Text)
    actif = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Relations
    # Le back_populates doit correspondre au nom de la relation dans Article
    piece = relationship("Article", back_populates="info_fournisseurs") 
    fournisseur = relationship("Fournisseur") # backref="info_pieces" dans Fournisseur si besoin

    def __repr__(self):
        return f"<PieceFournisseurInfo(piece_id={self.piece_id}, fournisseur_id={self.fournisseur_id}, ref='{self.reference_fournisseur}')>"