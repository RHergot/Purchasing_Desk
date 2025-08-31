# Fichier: app/views/select_supplier_dialog.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QListView, 
                               QDialogButtonBox, QLineEdit, QLabel)
from PySide6.QtCore import QStringListModel

class SelectSupplierDialog(QDialog):
    """
    A simple dialog to select a supplier from a list.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Select a Supplier"))
        self.setMinimumWidth(400)
        
        self.layout = QVBoxLayout(self)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("Search supplier..."))
        
        self.list_view = QListView()
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        self.layout.addWidget(QLabel(self.tr("Available Suppliers:")))
        self.layout.addWidget(self.search_input)
        self.layout.addWidget(self.list_view)
        self.layout.addWidget(self.button_box)
        
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)