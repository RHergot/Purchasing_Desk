# Fichier: app/views/ao_list_view.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableView, QPushButton, QAbstractItemView

class AoListView(QWidget):
    """
    View to display a list of open Requests for Quotation (Appels d'Offres).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.table_view = QTableView()
        self.table_view.setStyleSheet("font-size: 14px;")
        
        # Configuration de la sélection
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        
        self.table_view.setSortingEnabled(True)
        self.table_view.setAlternatingRowColors(True)
        
        # Boutons d'action pour cette vue
        self.refresh_button = QPushButton(self.tr("Refresh List"))
        self.refresh_button.setStyleSheet("font-size: 14px;")
        self.open_ao_button = QPushButton(self.tr("Open/Manage Selected RFQ..."))
        self.open_ao_button.setStyleSheet("font-size: 14px;")
        
        self.layout.addWidget(self.table_view)
        self.layout.addWidget(self.refresh_button)
        self.layout.addWidget(self.open_ao_button)