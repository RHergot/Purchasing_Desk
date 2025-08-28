from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableView, QComboBox,
    QPushButton, QDateEdit, QGroupBox, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, QDate


class OrdersKpiView(QWidget):
    """
    Vue KPI des commandes (Orders).
    - Filtres: période, fournisseur, pièce
    - KPIs: nb commandes, total HT, panier moyen
    - Tableaux: Top fournisseurs, Top pièces

    Cette vue ne contient pas de logique métier; le contrôleur injecte les modèles
    (QStandardItemModel) dans les QTableView et met à jour les labels KPI.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)

        # --- Filtres ---
        filters_box = QGroupBox(self.tr("Filters"))
        filters_layout = QHBoxLayout(filters_box)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-3))

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())

        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(False)
        self.supplier_combo.addItem(self.tr("All suppliers"), None)

        self.piece_combo = QComboBox()
        self.piece_combo.setEditable(False)
        self.piece_combo.addItem(self.tr("All items"), None)

        self.apply_button = QPushButton(self.tr("Apply"))

        filters_layout.addWidget(QLabel(self.tr("Start:")))
        filters_layout.addWidget(self.start_date_edit)
        filters_layout.addWidget(QLabel(self.tr("End:")))
        filters_layout.addWidget(self.end_date_edit)
        filters_layout.addWidget(QLabel(self.tr("Supplier:")))
        filters_layout.addWidget(self.supplier_combo)
        filters_layout.addWidget(QLabel(self.tr("Item:")))
        filters_layout.addWidget(self.piece_combo)
        filters_layout.addWidget(self.apply_button)

        main_layout.addWidget(filters_box)

        # --- KPI Cards (simples labels) ---
        kpi_box = QGroupBox(self.tr("Indicators"))
        kpi_layout = QHBoxLayout(kpi_box)

        self.orders_count_label = QLabel(self.tr("Orders: 0"))
        self.orders_total_ht_label = QLabel(self.tr("Total (excl. tax): 0"))
        self.orders_avg_basket_label = QLabel(self.tr("Average basket: 0"))

        for lbl in (self.orders_count_label, self.orders_total_ht_label, self.orders_avg_basket_label):
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
            lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            kpi_layout.addWidget(lbl)

        main_layout.addWidget(kpi_box)

        # --- Tables ---
        tables_row = QHBoxLayout()

        # Top fournisseurs
        suppliers_box = QGroupBox(self.tr("Top suppliers"))
        suppliers_layout = QVBoxLayout(suppliers_box)
        self.top_suppliers_table = QTableView()
        self.top_suppliers_table.setSelectionBehavior(QTableView.SelectRows)
        self.top_suppliers_table.setAlternatingRowColors(True)
        suppliers_layout.addWidget(self.top_suppliers_table)

        # Top pièces
        pieces_box = QGroupBox(self.tr("Top items"))
        pieces_layout = QVBoxLayout(pieces_box)
        self.top_pieces_table = QTableView()
        self.top_pieces_table.setSelectionBehavior(QTableView.SelectRows)
        self.top_pieces_table.setAlternatingRowColors(True)
        pieces_layout.addWidget(self.top_pieces_table)

        tables_row.addWidget(suppliers_box)
        tables_row.addWidget(pieces_box)

        main_layout.addLayout(tables_row)

        # Spacer
        main_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(main_layout)
