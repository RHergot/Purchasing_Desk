# Fichier: app/views/ao_detail_dialog.py

# Fichier: app/views/ao_detail_dialog.py (Version améliorée)

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
                               QTableView, QDialogButtonBox, QLabel, QGroupBox, QPushButton,
                               QSplitter, QWidget, QAbstractItemView)
from PySide6.QtCore import Qt

class AoDetailDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(self.tr("Manage Request for Quotation"))
        self.setMinimumSize(1000, 700)

        # --- Layouts ---
        self.main_layout = QVBoxLayout(self)
        # Un splitter pour redimensionner les zones
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # --- Colonne de Gauche (Infos et Fournisseurs) ---
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        
        # Groupe d'infos générales
        info_group = QGroupBox(self.tr("General Information"))
        self.form_layout = QFormLayout(info_group)
        self.ref_ao_label = QLineEdit()
        self.ref_ao_label.setReadOnly(True)
        self.titre_label = QLineEdit()
        self.titre_label.setReadOnly(True)
        self.form_layout.addRow(self.tr("RFQ Reference:"), self.ref_ao_label)
        self.form_layout.addRow(self.tr("Title:"), self.titre_label)
        self.left_layout.addWidget(info_group)

        # Groupe des fournisseurs
        suppliers_group = QGroupBox(self.tr("Consulted Suppliers"))
        suppliers_layout = QVBoxLayout(suppliers_group)
        self.suppliers_table_view = QTableView()
        # ==========================================================
        # === AJOUTS IMPORTANTS POUR LA SÉLECTION ==================
        # ==========================================================
        self.suppliers_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.suppliers_table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        # ==========================================================
        self.add_supplier_button = QPushButton(self.tr("Add Supplier..."))
        self.generate_supplier_rfq_pdf_button = QPushButton(self.tr("PDF for Selected Supplier"))
        self.generate_supplier_rfq_pdf_button.setEnabled(False) # Désactivé par défaut
        self.enter_offer_button = QPushButton(self.tr("Enter Supplier's Offer..."))
        self.enter_offer_button.setEnabled(False) # Désactivé par défaut
        self.generate_rfq_pdf_button = QPushButton(self.tr("Generate RFQ PDF (Generic)"))
        self.left_layout.addWidget(self.generate_rfq_pdf_button)
        suppliers_layout.addWidget(self.suppliers_table_view)
        supplier_buttons_layout = QHBoxLayout() # Créer un layout horizontal
        suppliers_layout.addLayout(supplier_buttons_layout) # Utiliser le layout horizontal
        suppliers_layout.addWidget(self.add_supplier_button)
        supplier_buttons_layout.addWidget(self.generate_supplier_rfq_pdf_button) # Ajout du nouveau bouton
        suppliers_layout.addWidget(self.enter_offer_button)
        self.left_layout.addWidget(suppliers_group)
        
        self.splitter.addWidget(self.left_panel)
        
        # --- Colonne de Droite (Tableau Comparatif) ---
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)

        # Groupe du tableau comparatif
        comparison_group = QGroupBox(self.tr("Offers Comparison"))
        comparison_layout = QVBoxLayout(comparison_group)
        self.comparison_table_view = QTableView()
        self.comparison_table_view.setAlternatingRowColors(True)
        comparison_layout.addWidget(self.comparison_table_view)
        self.right_layout.addWidget(comparison_group)

        self.splitter.addWidget(self.right_panel)
        
        # Redimensionnement initial
        self.splitter.setStretchFactor(0, 1) # Colonne de gauche prend 1/3
        self.splitter.setStretchFactor(1, 2) # Colonne de droite prend 2/3

        # --- Boutons de la dialogue ---
        self.button_box = QDialogButtonBox()
        self.finalize_button = self.button_box.addButton(self.tr("Finalize & Generate PO(s)"), QDialogButtonBox.AcceptRole)
        self.close_button = self.button_box.addButton(QDialogButtonBox.Close)
        
        self.main_layout.addWidget(self.button_box)
        self.close_button.clicked.connect(self.reject)