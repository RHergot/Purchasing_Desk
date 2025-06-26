from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableView, QLabel, QHBoxLayout, QPushButton, QSpacerItem, QSizePolicy, QComboBox, QDateEdit
from PySide6.QtCore import Qt, QDate

class NegotiationsView(QWidget):
    """
    View to display negotiation KPIs, showing savings made on purchases.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        
        self.layout = QVBoxLayout(self)
        
        # Titre
        title_label = QLabel(self.tr("<h2>Negotiation Savings Report</h2>"))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 14px;")
        self.layout.addWidget(title_label)
        

        # Layout for controls (like sort button)
        controls_layout = QHBoxLayout()
        self.toggle_sort_button = QPushButton(self.tr("Sort by Item Reference")) # Default text
        self.toggle_sort_button.setObjectName("toggleSortButton")
        self.toggle_sort_button.setStyleSheet("font-size: 14px;")
        controls_layout.addWidget(self.toggle_sort_button)
        controls_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        # === TESTS DE VISIBILITÉ ===
        self.toggle_sort_button.setMinimumHeight(30) # Lui donner une hauteur minimale
        self.toggle_sort_button.setVisible(True) # Forcer la visibilité (même si c'est par défaut)
        print(f"DEBUG VIEW: Toggle button created. Initial isVisible: {self.toggle_sort_button.isVisible()}")
        # ===========================

        controls_layout.addWidget(self.toggle_sort_button)
        controls_layout.addStretch() # Push button to the left, or add other controls later
        self.layout.addLayout(controls_layout)
        
        # Table View pour afficher les détails
        self.table_view = QTableView()
        self.table_view.setStyleSheet("font-size: 14px;")
        self.table_view.setSortingEnabled(True)
        self.table_view.setAlternatingRowColors(True)
        self.layout.addWidget(self.table_view)

        controls_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))

        # --- NOUVEAU FILTRE MACHINE ---
        controls_layout.addWidget(QLabel(self.tr("Machine:")))
        self.machine_filter_combo = QComboBox()
        self.machine_filter_combo.setMinimumWidth(150)
        controls_layout.addWidget(self.machine_filter_combo)
        # --- FIN FILTRE MACHINE ---
        
        # Zone pour afficher les totaux
        summary_layout = QHBoxLayout()
        summary_layout.addStretch() # Pour pousser les labels à droite
        
        self.total_savings_label_title = QLabel(self.tr("<b>Total Savings Achieved:</b>"))
        self.total_savings_value_label = QLabel(self.tr("0.00 EUR")) # Valeur par défaut
        self.total_savings_value_label.setStyleSheet("font-weight: bold; color: green;")

        # --- NOUVEAU FILTRE FOURNISSEUR ---
        controls_layout.addWidget(QLabel(self.tr("Filter by Supplier:")))
        self.supplier_filter_combo = QComboBox()
        self.supplier_filter_combo.setMinimumWidth(150)
        controls_layout.addWidget(self.supplier_filter_combo)
        # --- FIN FILTRE FOURNISSEUR ---

        controls_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))

        # --- NOUVEAU FILTRE PIÈCE ---
        controls_layout.addWidget(QLabel(self.tr("Item Ref:")))
        self.piece_filter_combo = QComboBox()
        self.piece_filter_combo.setMinimumWidth(150)
        controls_layout.addWidget(self.piece_filter_combo)
        # --- FIN FILTRE PIÈCE ---

        controls_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))

        # --- NOUVEAU FILTRE PLAGE DE DATES ---
        controls_layout.addWidget(QLabel(self.tr("From:")))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-3)) # Par défaut, les 3 derniers mois
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        controls_layout.addWidget(self.start_date_edit)

        controls_layout.addWidget(QLabel(self.tr("To:")))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate()) # Par défaut, aujourd'hui
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        controls_layout.addWidget(self.end_date_edit)
        # --- FIN FILTRE PLAGE DE DATES ---


        controls_layout.addStretch()
        self.layout.addLayout(controls_layout)

        summary_layout.addWidget(self.total_savings_label_title)
        summary_layout.addWidget(self.total_savings_value_label)
        self.layout.addLayout(summary_layout)

        # Boutons d'action (Fermer, Optionnel: Exporter, Rafraîchir)
        action_button_layout = QHBoxLayout()
        action_button_layout.addStretch() # Pousser les boutons à droite

        # Optionnel : Boutons pour exporter, rafraîchir
        self.refresh_button = QPushButton(self.tr("Refresh Data"))
        self.export_button = QPushButton(self.tr("Export to CSV"))

        self.close_button = QPushButton(self.tr("Close"))
        self.close_button.clicked.connect(lambda: self.window().close()) # Utilise un lambda pour garantir la fermeture correcte de la fenêtre
        action_button_layout.addWidget(self.close_button)
        action_button_layout.addWidget(self.refresh_button)
        action_button_layout.addWidget(self.export_button)

        self.layout.addLayout(action_button_layout)