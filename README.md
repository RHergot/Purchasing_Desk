# Purchasing_Desk
Application de bureau de gestion des achats (Purchasing Desk) basée sur PySide6 (Qt), SQLAlchemy et génération de PDF avec Jinja2 + wkhtmltopdf. L'application suit une architecture de type MVC (views/controllers/models) et se connecte à une base de données PostgreSQL.

## Sommaire
- Présentation
- Architecture & Structure
- Pré-requis
- Configuration (.env)
- Initialisation de la base de données
- Lancer l'application
- Génération de PDF (wkhtmltopdf)
- Dépannage (Troubleshooting)

## Présentation
- **Interface**: `PySide6` pour l'UI Qt.
- **Données**: `SQLAlchemy` (ORM) vers PostgreSQL.
- **Config**: `python-dotenv` lit `.env` via `config.py` et construit l'URL DB.
- **PDF**: `Jinja2` (templates HTML) + `pdfkit` (wkhtmltopdf) pour les commandes (PO) et appels d'offres (RFQ).

Entrée principale: `main.py` crée l'application Qt, vérifie la connexion DB (via `database.engine`) puis affiche `MainWindow`.

## Architecture & Structure
- `main.py`:
  - Classe `MainWindow` avec menu (KPI, Catalogue, etc.) et `QTabWidget` central.
  - Onglets principaux:
    - "Draft Orders": `PurchaseRequisitionView` + `PurchaseRequisitionController`
    - "Open RFQs": `AoListView` + `AoListController`
  - Fenêtres additionnelles:
    - KPI Négociations: `NegotiationsView` + `NegotiationsController`
    - Catalogue pièces: `PieceListView` + `PieceListController`
  - Sur changement d'onglet: `refresh_current_tab()` recharge les données via les contrôleurs.

- `config.py`:
  - Charge `.env` avec `load_dotenv()` et expose `config.DATABASE_URL` (PostgreSQL via `psycopg2`).

- `database.py`:
  - Initialise `engine`, `SessionLocal`, `Base` et fournit `get_db_session()` (yield + fermeture en `finally`).

- `app/`:
  - `views/`: Widgets et dialogues Qt.
  - `controllers/`: Connexion signaux/slots, requêtes de données, peuplement des modèles Qt (`QStandardItemModel`).
  - `models/`: Modèles SQLAlchemy (ex: `Commande`, `LigneCommande`, `AppelOffre`, `Fournisseur`, etc.).
  - `templates/`: Templates Jinja2 pour les PDF (`rfq_template.html`, etc.).
  - `utils/pdf_generator.py`:
    - Environnement Jinja2 et filtre `nl2br`.
    - Configuration robuste de wkhtmltopdf (chemin explicite Windows puis fallback PATH).
    - `generate_purchase_order_pdf(commande_id, parent_widget=None)`.
    - `generate_rfq_pdf(ao_id, fournisseur_id_destinataire=None, parent_widget=None)`.

## Pré-requis
- Python 3.10+ recommandé.
- PostgreSQL accessible avec une base et un utilisateur.
- wkhtmltopdf installé côté OS.

## Dépendances Python
Le fichier `requirements.txt` doit inclure au minimum:

```
PySide6
SQLAlchemy
psycopg2-binary
python-dotenv
Jinja2
pdfkit
```

Installez-les dans un virtualenv:

```
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Configuration (.env)
Créer un fichier `.env` à la racine (existe déjà dans ce projet) avec:

```
DB_HOST=your-db-host
DB_PORT=5432
DB_NAME=your-db-name
DB_USER=your-db-user
DB_PASSWORD=your-db-password
```

`config.py` construit l'URL: `postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}`.

## Initialisation de la base de données
- Exécuter le script SQL fourni `setup_tables.sql` sur votre base PostgreSQL pour créer les tables nécessaires.
- Vérifiez les droits de l'utilisateur (création/lecture/écriture selon besoins).

## Lancer l'application

```
python main.py
```

Au démarrage, `main.py` tente une connexion à la DB via `database.engine`. En cas d'échec, un `QMessageBox` s'affiche et l'application se ferme proprement.

## Génération de PDF (wkhtmltopdf)
- `app/utils/pdf_generator.py` recherche l'exécutable wkhtmltopdf:
  1) Chemin explicite Windows: `C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe`
  2) Sinon via le `PATH` du système
- En cas d'absence, un message d'erreur GUI est affiché et la génération retourne `False`.
- Les templates se trouvent dans `app/templates/`. Vérifiez la présence de `rfq_template.html` et du template de commande (PO).

## Dépannage
- **Connexion DB échouée**: vérifiez `.env`, la connectivité réseau, que la base existe et que les tables sont créées (`setup_tables.sql`).
- **PDF non généré**: installez wkhtmltopdf ou ajustez le chemin explicite dans `app/utils/pdf_generator.py`. Assurez-vous que `pdfkit` est installé.
- **UI vide ou données absentes**: lancez l'appli dans un terminal pour voir les logs (prints) et vérifiez les contrôleurs sous `app/controllers/`.
- **Dépendances manquantes**: mettez à jour `requirements.txt` (voir section Dépendances Python) puis `pip install -r requirements.txt`.

## Tests
Le dossier `tests/` existe. Complétez/ajoutez des tests pour couvrir les contrôleurs et utilitaires.

---

© Purchasing Desk — usage interne. Ajoutez licence/mentions légales si nécessaire.