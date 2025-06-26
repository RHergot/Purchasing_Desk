# Fichier: app/views/piece_filter_dialog.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QComboBox, 
                               QDialogButtonBox, QLabel, QRadioButton, QButtonGroup,
                               QWidget, QHBoxLayout, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt

from database import get_db_session
from app.models.shared_models import Machine, Fournisseur, Article, PieceExtension # Article est notre 'piece'

class PieceFilterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Filter Pieces Catalogue"))
        self.setMinimumWidth(450)

        self.layout = QVBoxLayout(self)
        
        # Groupe pour le choix du critère principal
        self.criteria_group = QButtonGroup(self) # Assure qu'un seul radio est coché
        
        # Critère : Toutes les pièces (avec statut actif)
        self.all_pieces_radio = QRadioButton(self.tr("All Active Pieces"))
        self.criteria_group.addButton(self.all_pieces_radio)
        self.layout.addWidget(self.all_pieces_radio)

        # Critère : Par Machine
        machine_layout = QHBoxLayout()
        self.machine_radio = QRadioButton(self.tr("By Machine:"))
        self.machine_combo = QComboBox()
        self.machine_combo.setEnabled(False) # Désactivé par défaut
        machine_layout.addWidget(self.machine_radio)
        machine_layout.addWidget(self.machine_combo)
        self.criteria_group.addButton(self.machine_radio)
        self.layout.addLayout(machine_layout)

        # Critère : Par Fournisseur Préféré
        supplier_layout = QHBoxLayout()
        self.supplier_radio = QRadioButton(self.tr("By Preferred Supplier:"))
        self.supplier_combo = QComboBox()
        self.supplier_combo.setEnabled(False) # Désactivé par défaut
        supplier_layout.addWidget(self.supplier_radio)
        supplier_layout.addWidget(self.supplier_combo)
        self.criteria_group.addButton(self.supplier_radio)
        self.layout.addLayout(supplier_layout)

        # Critère : Par Catégorie
        category_layout = QHBoxLayout()
        self.category_radio = QRadioButton(self.tr("By Category:"))
        self.category_combo = QComboBox()
        self.category_combo.setEnabled(False) # Désactivé par défaut
        category_layout.addWidget(self.category_radio)
        category_layout.addWidget(self.category_combo)
        self.criteria_group.addButton(self.category_radio)
        self.layout.addLayout(category_layout)
        
        # Critère : Stock en Alerte
        self.stock_alert_radio = QRadioButton(self.tr("Items with Stock Alert"))
        self.criteria_group.addButton(self.stock_alert_radio)
        self.layout.addWidget(self.stock_alert_radio)

        self.layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.layout.addWidget(self.button_box)

        # Connexions pour activer/désactiver les ComboBox
        self.machine_radio.toggled.connect(self.machine_combo.setEnabled)
        self.supplier_radio.toggled.connect(self.supplier_combo.setEnabled)
        self.category_radio.toggled.connect(self.category_combo.setEnabled)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.populate_combos()
        self.all_pieces_radio.setChecked(True) # Choix par défaut

    def populate_combos(self):
        session = next(get_db_session())
        try:
            self.machine_combo.addItem(self.tr("All Machines"), None)
            self.supplier_combo.addItem(self.tr("All Suppliers"), None)
            self.category_combo.addItem(self.tr("All Categories"), None)
            
            # Populate Machines (uniquement celles liées à des pièces via piece_extension)
            machines = session.query(Machine.id_machine, Machine.nom)\
                              .join(PieceExtension, Machine.id_machine == PieceExtension.machine_id)\
                              .distinct().order_by(Machine.nom).all()
            for id_machine, nom in machines:
                self.machine_combo.addItem(nom, id_machine)

            # Populate Suppliers (ceux qui sont fournisseur_pref_id dans piece)
            pref_suppliers = session.query(Fournisseur.id_fournisseur, Fournisseur.nom)\
                                    .join(Article, Fournisseur.id_fournisseur == Article.fournisseur_id_default)\
                                    .distinct().order_by(Fournisseur.nom).all()
            for id_fournisseur, nom in pref_suppliers:
                self.supplier_combo.addItem(nom, id_fournisseur)

            # Populate Categories
            categories = session.query(Article.categorie)\
                                .filter(Article.categorie.isnot(None), Article.categorie != '')\
                                .distinct().order_by(Article.categorie).all()
            for cat in categories:
                self.category_combo.addItem(cat[0], cat[0])
        except Exception as e:
            print(f"Error populating filter combos: {e}")
            # Vous pourriez vouloir afficher un QMessageBox ici en cas d'erreur
        finally:
            session.close()

    def get_selected_filter(self):
        """
        Returns a tuple: (filter_type, filter_value)
        filter_type can be: 'all', 'machine', 'supplier', 'category', 'stock_alert'
        filter_value is the ID or name, or None if not applicable.
        """
        if self.machine_radio.isChecked():
            return 'machine', self.machine_combo.currentData()
        elif self.supplier_radio.isChecked():
            return 'supplier', self.supplier_combo.currentData()
        elif self.category_radio.isChecked():
            return 'category', self.category_combo.currentData() # ou .currentText() si vous n'avez pas mis d'ID
        elif self.stock_alert_radio.isChecked():
            return 'stock_alert', None
        elif self.all_pieces_radio.isChecked():
            return 'all', None
        return None, None # Ne devrait pas arriver si un radio est toujours coché