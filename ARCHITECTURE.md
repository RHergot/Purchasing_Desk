# 🏗️ Architecture — Purchasing Desk

**Application de gestion des achats (Purchasing Desk)**  
Date : 2026-07-05 | Version : 1.0 (Phase 4)

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Stack technique](#2-stack-technique)
3. [Architecture MVC](#3-architecture-mvc)
4. [Arborescence du projet](#4-arborescence-du-projet)
5. [Base de données](#5-base-de-données)
6. [Workflows métier](#6-workflows-métier)
7. [Système KPI](#7-système-kpi)
8. [Génération PDF](#8-génération-pdf)
9. [Sécurité & Configuration](#9-sécurité--configuration)
10. [Qualité & Tests](#10-qualité--tests)

---

## 1. Vue d'ensemble

Purchasing Desk est une **application de bureau PySide6** couvrant le cycle complet des achats industriels :

```
Brouillon commande → RFQ (Appel d'Offres) → Offres fournisseurs
        → Comparaison → Commande finale (BC) → PDF
```

L'application s'intègre à un écosystème GMAO (Gestion de Maintenance Assistée par Ordinateur) existant et partage sa base de données PostgreSQL.

### Modules fonctionnels

| Module | Description |
|--------|-------------|
| **Draft Orders** | Gestion des brouillons de commandes, conversion en RFQ |
| **Open RFQs** | Liste des appels d'offres ouverts, consultation et détail |
| **RFQ Detail** | Ajout fournisseurs, saisie offres, comparaison, finalisation |
| **Negotiations KPI** | Analyse des économies par négociation (prix référence vs réel) |
| **Orders KPI** | Statistiques de commandes : volumes, top fournisseurs, top articles |
| **Financial KPI** | Dépenses totales, savings par RFQ, tendance des prix |
| **Piece Catalogue** | Consultation du catalogue de pièces |

---

## 2. Stack technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Langage | Python 3 | ≥ 3.9 |
| GUI Framework | PySide6 (Qt 6) | ≥ 6.5.0 |
| ORM | SQLAlchemy | ≥ 2.0.0 |
| Base de données | PostgreSQL | ≥ 13 |
| Driver PostgreSQL | psycopg2-binary | ≥ 2.9.0 |
| Génération PDF | Jinja2 + pdfkit (wkhtmltopdf) | ≥ 3.1.2 / ≥ 1.0.0 |
| Validation | Pydantic | ≥ 2.0.0 |
| Tests | pytest | ≥ 7.0.0 |
| Migrations DB | Alembic | ≥ 1.12.0 |
| Export | openpyxl (Excel) + csv (stdlib) | ≥ 3.0.0 |
| Sécurité | bcrypt, python-dotenv | ≥ 4.0.0 / ≥ 1.0.0 |

---

## 3. Architecture MVC

L'application suit le pattern **Model-View-Controller** :

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Models     │     │   Controllers    │     │     Views       │
│ (SQLAlchemy) │◄────│ (logique métier) │────►│ (PySide6 UI)    │
└──────────────┘     └──────────────────┘     └─────────────────┘
       ▲                       │                       │
       │                       ▼                       │
       │              ┌──────────────────┐             │
       └──────────────│    database.py    │             │
                      │ (connexion + pool)│             │
                      └──────────────────┘             │
                              │                        │
                              ▼                        │
                     ┌──────────────────┐             │
                     │   PostgreSQL     │             │
                     └──────────────────┘             │
```

### Flux de données

1. L'utilisateur interagit avec une **View** (QWidget/QDialog)
2. La View émet des **signaux Qt** capturés par le **Controller**
3. Le Controller interroge/modifie la base via **SQLAlchemy**
4. Le Controller met à jour le **Model** (QStandardItemModel) lié à la View
5. La View se rafraîchit automatiquement

---

## 4. Arborescence du projet

```
Purchasing_Desk/
├── main.py                          # Point d'entrée, QApplication, MainWindow
├── config.py                        # Configuration (DB, env vars)
├── database.py                      # Engine SQLAlchemy, pool, get_db_session()
├── requirements.txt                 # Dépendances Python
├── setup.sh                         # Script d'installation automatisé
├── setup_all_tables.sql             # Script SQL complet de création du schéma
├── alembic.ini                      # Configuration Alembic
├── alembic/                         # Migrations de base de données
│   ├── env.py                       # Configuration Alembic (target_metadata)
│   └── versions/
│       └── 001_initial_schema.py    # Migration initiale (toutes les tables)
├── ARCHITECTURE.md                  # Ce document
├── app/
│   ├── __init__.py                  # Imports publics
│   ├── controllers/
│   │   ├── __init__.py              # Imports publics des contrôleurs
│   │   ├── pr_controller.py         # Purchase Requisition (brouillons → RFQ)
│   │   ├── ao_list_controller.py    # Liste des appels d'offres
│   │   ├── ao_detail_controller.py  # Détail AO : fournisseurs, offres, comparaison
│   │   ├── negotiations_controller.py # KPI Négociations
│   │   ├── orders_kpi_controller.py   # KPI Commandes
│   │   ├── financial_kpi_controller.py # KPI Financiers
│   │   └── piece_list_controller.py   # Catalogue de pièces
│   ├── models/
│   │   ├── shared_models.py         # Fournisseur, Machine, Utilisateur, Article, etc.
│   │   └── purchase_models.py       # Commande, LigneCommande, AppelOffre, OffreRecue, etc.
│   ├── views/
│   │   ├── pr_view.py               # Vue brouillons de commande
│   │   ├── ao_list_view.py          # Vue liste des AOs
│   │   ├── ao_detail_view.py        # Vue détail AO
│   │   ├── select_supplier_dialog.py # Dialogue sélection fournisseur
│   │   ├── enter_offer_dialog.py    # Dialogue saisie d'offre
│   │   ├── piece_list_view.py       # Vue catalogue pièces
│   │   ├── negotiations_view.py     # Vue KPI Négociations
│   │   ├── orders_kpi_view.py       # Vue KPI Commandes
│   │   ├── financial_kpi_view.py    # Vue KPI Financiers
│   │   └── price_comparison_view.py # Dialogue comparaison de prix
│   ├── utils/
│   │   ├── kpi_helpers.py           # PopulateFiltersMixin, line_total()
│   │   └── pdf_generator.py         # Génération PDF (BC, RFQ), config wkhtmltopdf
│   ├── validators/
│   │   ├── __init__.py
│   │   └── order_validators.py      # Pydantic : Commande, LigneCommande, AO, etc.
│   ├── auth/
│   │   └── __init__.py              # AuthManager, rôles, bcrypt
│   ├── export/
│   │   └── __init__.py              # CSV/Excel export pour KPIs
│   └── templates/
│       ├── order_template.html      # Template Jinja2 pour bon de commande
│       └── rfq_template.html        # Template Jinja2 pour appel d'offres
└── tests/
    ├── __init__.py
    ├── test_kpi_helpers.py          # Tests unitaires des utilitaires KPI
    ├── test_models.py               # Tests des modèles SQLAlchemy
    └── test_validators.py           # Tests des validateurs Pydantic
```

---

## 5. Base de données

### Schéma

Le schéma utilise le namespace **`public`** de PostgreSQL. Toutes les tables sont dans ce schéma.

### Tables principales (13 tables)

| Table | Modèle Python | Description |
|-------|--------------|-------------|
| `fournisseur` | `Fournisseur` | Fournisseurs (nom, email, adresse, devise) |
| `machine` | `Machine` | Machines de production |
| `utilisateur` | `Utilisateur` | Utilisateurs (nom, role, login, email) |
| `piece` | `Article` | Pièces/articles (référence, désignation, stock) |
| `piece_extension` | `PieceExtension` | Extensions pièce (machine, emplacement, catégorie) |
| `piece_fournisseur_info` | `PieceFournisseurInfo` | Références et prix fournisseurs par pièce |
| `commande` | `Commande` | Commandes d'achat |
| `ligne_commande` | `LigneCommande` | Lignes de commande |
| `appel_offre` | `AppelOffre` | Appels d'offres (RFQ) |
| `ao_fournisseur_consulte` | `AoFournisseurConsulte` | Fournisseurs consultés par RFQ |
| `offre_recue` | `OffreRecue` | Offres reçues |
| `offre_recue_ligne` | `OffreRecueLigne` | Lignes d'offre (prix proposés) |
| `contrat_achat` | `ContratAchat` | Contrats d'achat |
| `prestation_achat` | `PrestationAchat` | Prestations externes |

### Connexion

La connexion est gérée par `database.py` :
- **Engine** : `create_engine(url, pool_size=5, max_overflow=10, pool_recycle=3600, pool_pre_ping=True)`
- **Session** : `SessionLocal` via `get_db_session()` (générateur, fermeture automatique)
- **URL** : Construite depuis `config.py` → `postgresql+psycopg2://` avec variables d'environnement
- **Validation** : `config.validate()` vérifie que toutes les variables requises sont définies

---

## 6. Workflows métier

### Workflow principal : Brouillon → Commande

```
1. [pr_controller]    Création brouillon de commande (statut: Brouillon)
2. [pr_controller]    Start RFQ → création AppelOffre (statut commande: Validee)
3. [ao_detail]        Ajout fournisseurs consultés (AoFournisseurConsulte)
4. [ao_detail]        Saisie des offres (OffreRecue + OffreRecueLigne)
5. [ao_detail]        Comparaison des offres (build_comparison_table)
6. [ao_detail]        Sélection du meilleur prix par ligne
7. [ao_detail]        Finalisation → création Commande (statut: Envoyee)
8. [pdf_generator]    Génération PDF du bon de commande
```

### États d'une commande

```
Brouillon → Validee → [RFQ lancé]
                    → Envoyee → Partielle → Livree
                    → Annulee
```

---

## 7. Système KPI

Trois modules KPI indépendants, accessibles via le menu :

### 7.1 Orders KPI (`orders_kpi_controller`)
- Nombre de commandes par période
- Total HT dépensé
- Panier moyen
- Top 20 fournisseurs (par CA)
- Top 50 articles (par CA, quantités)

### 7.2 Financial KPI (`financial_kpi_controller`)
- Dépenses totales (somme ligne_commande.prix_unitaire_ht × quantite)
- Savings : (prix moyen des offres - prix sélectionné) × quantité
- Taux de savings (%)
- Table des savings par RFQ
- Tendance des prix moyens par article

### 7.3 Negotiations KPI (`negotiations_controller`)
- Comparaison prix de référence (piece.prix_unitaire) vs prix négocié (ligne_commande.prix_unitaire_ht)
- Économies unitaires et totales par ligne
- Deux modes de tri : par commande / par pièce (avec regroupement)
- Filtres : fournisseur, pièce, machine, période
- Export CSV

### Filtres communs
Tous les KPI ont des filtres :
- **Période** (date début → date fin)
- **Fournisseur** (QComboBox)
- **Pièce** (QComboBox)
- **Debounce 300ms** sur les changements de filtre

---

## 8. Génération PDF

La génération PDF utilise :
- **Jinja2** pour le rendu HTML des templates
- **pdfkit** (wrapper Python de wkhtmltopdf) pour la conversion HTML → PDF

### Templates
- `order_template.html` : Bon de commande (BC)
  - Infos entreprise dynamiques (env vars : COMPANY_NAME, COMPANY_ADDRESS, etc.)
  - Détail des lignes, totaux, conditions
- `rfq_template.html` : Appel d'offres
  - Personnalisable par fournisseur destinataire
  - Références fournisseur connues incluses

### Sécurité wkhtmltopdf
- `--disable-javascript`
- `--disable-local-file-access`
- Filtre `nl2br` pour les sauts de ligne

### Fallback
Si wkhtmltopdf n'est pas trouvé au chemin explicite, recherche dans le PATH système.

---

## 9. Sécurité & Configuration

### Configuration
- **Variables d'environnement** : DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
- **Fichier `.env`** optionnel (chargé par python-dotenv)
- **Validation** au démarrage : `config.validate()` → exit si variables manquantes
- **Company info** pour PDF : COMPANY_NAME, COMPANY_ADDRESS, etc.

### Pool de connexions
- `pool_size=5`, `max_overflow=10`, `pool_recycle=3600`
- `pool_pre_ping=True` (vérification avant utilisation)

### Authentification
- Module `app/auth/` : `AuthManager`, constantes de rôles
- Rôles : admin, acheteur, maintenance, lecteur
- Permissions fines par action (créer commande, finaliser, voir KPI, exporter…)
- bcrypt pour le hachage des mots de passe

### Bonnes pratiques
- Toutes les sessions SQLAlchemy sont fermées dans `finally`
- Logging structuré (DEBUG → purchasing_desk.log + console)
- Exception hook global Qt (catch unhandled exceptions)
- HiDPI activé avant création de QApplication

---

## 10. Qualité & Tests

### Tests unitaires (44 tests)
- **test_kpi_helpers.py** : `line_total()`, calculs Decimal, cas limites
- **test_models.py** : Metadata des modèles (noms de tables, colonnes, contraintes, FKs)
- **test_validators.py** : Validateurs Pydantic (création commande, ligne, AO, fournisseur)

### Validation de données
- **Pydantic** (`app/validators/`) : `CommandeCreate`, `LigneCommandeCreate`, `AppelOffreCreate`, etc.
- Validation des champs obligatoires, types, contraintes métier
- Énumérations partagées entre validateurs et modèles SQLAlchemy

### Migrations
- **Alembic** : gestion versionnée du schéma
- Migration initiale `001_initial_schema.py` : toutes les tables + enums

### Exports
- **CSV** : export de n'importe quel QStandardItemModel
- **Excel** (openpyxl) : export multi-feuilles avec auto-sizing des colonnes

---

*Document généré automatiquement — Phase 4 Purchasing Desk — 2026-07-05*
