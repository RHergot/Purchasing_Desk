from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableView, QComboBox,
    QPushButton, QDateEdit, QGroupBox, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, QDate


class FinancialKpiView(QWidget):
    """
    Vue KPI financière.
    - Filtres: période, fournisseur, pièce
    - KPIs: Spend total, Savings total, Taux de savings
    - Tableaux/graphes: Savings par AO (tableau), Evolution prix moyen (placeholder table)

    Le contrôleur fournit les modèles et met à jour les étiquettes KPI.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)

        # --- Filtres ---
        filters_box = QGroupBox(self.tr("Filtres"))
        filters_layout = QHBoxLayout(filters_box)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-6))

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())

        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(False)
        self.supplier_combo.addItem(self.tr("Tous les fournisseurs"), None)

        self.piece_combo = QComboBox()
        self.piece_combo.setEditable(False)
        self.piece_combo.addItem(self.tr("Toutes les pièces"), None)

        self.apply_button = QPushButton(self.tr("Appliquer"))

        filters_layout.addWidget(QLabel(self.tr("Début:")))
        filters_layout.addWidget(self.start_date_edit)
        filters_layout.addWidget(QLabel(self.tr("Fin:")))
        filters_layout.addWidget(self.end_date_edit)
        filters_layout.addWidget(QLabel(self.tr("Fournisseur:")))
        filters_layout.addWidget(self.supplier_combo)
        filters_layout.addWidget(QLabel(self.tr("Pièce:")))
        filters_layout.addWidget(self.piece_combo)
        filters_layout.addWidget(self.apply_button)

        main_layout.addWidget(filters_box)

        # --- KPI Cards ---
        kpi_box = QGroupBox(self.tr("Indicateurs"))
        kpi_layout = QHBoxLayout(kpi_box)

        self.spend_total_label = QLabel(self.tr("Spend total: 0"))
        self.savings_total_label = QLabel(self.tr("Savings: 0"))
        self.savings_rate_label = QLabel(self.tr("Taux de savings: 0%"))

        for lbl in (self.spend_total_label, self.savings_total_label, self.savings_rate_label):
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
            lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            kpi_layout.addWidget(lbl)

        main_layout.addWidget(kpi_box)

        # --- Tables ---
        tables_row = QHBoxLayout()

        # Savings par AO
        savings_box = QGroupBox(self.tr("Savings par AO"))
        savings_layout = QVBoxLayout(savings_box)
        self.savings_table = QTableView()
        self.savings_table.setSelectionBehavior(QTableView.SelectRows)
        self.savings_table.setAlternatingRowColors(True)
        savings_layout.addWidget(self.savings_table)

        # Evolution prix moyen (placeholder tableau)
        trend_box = QGroupBox(self.tr("Evolution prix moyen"))
        trend_layout = QVBoxLayout(trend_box)
        self.price_trend_table = QTableView()
        self.price_trend_table.setSelectionBehavior(QTableView.SelectRows)
        self.price_trend_table.setAlternatingRowColors(True)
        trend_layout.addWidget(self.price_trend_table)

        tables_row.addWidget(savings_box)
        tables_row.addWidget(trend_box)

        main_layout.addLayout(tables_row)

        # Spacer
        main_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(main_layout)
