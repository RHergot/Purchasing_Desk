# Fichier: app/views/pr_view.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableView, QPushButton, QAbstractItemView

class PurchaseRequisitionView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.table_view = QTableView()
        
        # ==========================================================
        # === AJOUTS IMPORTANTS POUR LA SÉLECTION ==================
        # ==========================================================
        # 1. Sélectionner des lignes entières, pas des cellules
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 2. Ne permettre la sélection que d'une seule ligne à la fois
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        # ==========================================================

        self.table_view.setSortingEnabled(True)
        self.table_view.setAlternatingRowColors(True)
        
        self.refresh_button = QPushButton(self.tr("Refresh List"))
        self.create_po_button = QPushButton(self.tr("Process Selected Order..."))
        
        self.layout.addWidget(self.table_view)
        self.layout.addWidget(self.refresh_button)
        self.layout.addWidget(self.create_po_button)
