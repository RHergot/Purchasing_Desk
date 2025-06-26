# Fichier: app/views/piece_list_view.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableView, QLabel, QPushButton, QHBoxLayout, QAbstractItemView
from PySide6.QtCore import Qt

class PieceListView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        
        # Zone pour les contrôles (bouton de filtre)
        controls_layout = QHBoxLayout()
        self.filter_button = QPushButton(self.tr("Define Filters..."))
        controls_layout.addWidget(self.filter_button)
        self.close_button = QPushButton(self.tr("Close"))
        self.close_button.clicked.connect(lambda: self.window().close()) # Utilise un lambda pour garantir la fermeture correcte de la fenêtre
        controls_layout.addWidget(self.close_button)
        controls_layout.addStretch()
        self.layout.addLayout(controls_layout)

        # Label pour afficher les filtres actifs
        self.active_filters_label = QLabel(self.tr("Current Filter: All Active Pieces"))
        self.active_filters_label.setStyleSheet("font-style: italic; color: grey;")
        self.layout.addWidget(self.active_filters_label)
        
        # Tableau des pièces
        self.table_view = QTableView()
        self.table_view.setSortingEnabled(True)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows) # Si besoin de sélectionner
        self.layout.addWidget(self.table_view)