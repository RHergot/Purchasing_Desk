# Fichier: app/views/price_comparison_view.py
"""
Price Comparison View — standalone QDialog for managing RFQ supplier offers
and comparing prices to select the best offers.

This view is designed to work with AoDetailController which expects a dialog
with the following widgets accessible as attributes:
  - ref_ao_label, titre_label         (QLineEdit, read-only)
  - suppliers_table_view              (QTableView)
  - comparison_table_view             (QTableView)
  - add_supplier_button               (QPushButton)
  - enter_offer_button                (QPushButton, disabled by default)
  - generate_rfq_pdf_button           (QPushButton)
  - generate_supplier_rfq_pdf_button  (QPushButton, disabled by default)
  - button_box                        (QDialogButtonBox)
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QTableView, QDialogButtonBox, QLabel, QGroupBox, QPushButton,
    QSplitter, QWidget, QAbstractItemView,
)
from PySide6.QtCore import Qt


class PriceComparisonDialog(QDialog):
    """
    Dialog for managing the RFQ price comparison workflow.

    Displays general RFQ information, the list of consulted suppliers,
    and a comparison table of received offers. Provides actions to
    add suppliers, enter offers, generate RFQ PDFs, and finalize
    purchase orders from selected offers.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(self.tr("Price Comparison — Manage RFQ"))
        self.setMinimumSize(1000, 700)

        # --- Main layout ---
        self.main_layout = QVBoxLayout(self)

        # Splitter for resizable left/right panels
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # ================================================================
        # LEFT PANEL — General Info + Supplier List
        # ================================================================
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)

        # --- General Information group ---
        info_group = QGroupBox(self.tr("General Information"))
        self.form_layout = QFormLayout(info_group)
        self.ref_ao_label = QLineEdit()
        self.ref_ao_label.setReadOnly(True)
        self.titre_label = QLineEdit()
        self.titre_label.setReadOnly(True)
        self.form_layout.addRow(self.tr("RFQ Reference:"), self.ref_ao_label)
        self.form_layout.addRow(self.tr("Title:"), self.titre_label)
        self.left_layout.addWidget(info_group)

        # --- Consulted Suppliers group ---
        suppliers_group = QGroupBox(self.tr("Consulted Suppliers"))
        suppliers_layout = QVBoxLayout(suppliers_group)

        self.suppliers_table_view = QTableView()
        self.suppliers_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.suppliers_table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.suppliers_table_view.setAlternatingRowColors(True)

        self.add_supplier_button = QPushButton(self.tr("Add Supplier..."))

        # Supplier action buttons (horizontal row)
        supplier_buttons_layout = QHBoxLayout()
        self.generate_supplier_rfq_pdf_button = QPushButton(
            self.tr("PDF for Selected Supplier")
        )
        self.generate_supplier_rfq_pdf_button.setEnabled(False)
        self.enter_offer_button = QPushButton(self.tr("Enter Supplier's Offer..."))
        self.enter_offer_button.setEnabled(False)
        supplier_buttons_layout.addWidget(self.generate_supplier_rfq_pdf_button)
        supplier_buttons_layout.addWidget(self.enter_offer_button)

        self.generate_rfq_pdf_button = QPushButton(
            self.tr("Generate RFQ PDF (Generic)")
        )

        suppliers_layout.addWidget(self.suppliers_table_view)
        suppliers_layout.addLayout(supplier_buttons_layout)
        suppliers_layout.addWidget(self.add_supplier_button)
        self.left_layout.addWidget(suppliers_group)

        self.splitter.addWidget(self.left_panel)

        # ================================================================
        # RIGHT PANEL — Comparison Table
        # ================================================================
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)

        comparison_group = QGroupBox(self.tr("Offers Comparison"))
        comparison_layout = QVBoxLayout(comparison_group)
        self.comparison_table_view = QTableView()
        self.comparison_table_view.setAlternatingRowColors(True)
        comparison_layout.addWidget(self.comparison_table_view)
        self.right_layout.addWidget(comparison_group)

        self.splitter.addWidget(self.right_panel)

        # Splitter proportions: left 1/3, right 2/3
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)

        # --- Bottom button box ---
        self.button_box = QDialogButtonBox()
        self.finalize_button = self.button_box.addButton(
            self.tr("Finalize & Generate PO(s)"), QDialogButtonBox.AcceptRole
        )
        self.close_button = self.button_box.addButton(QDialogButtonBox.Close)

        self.main_layout.addWidget(self.button_box)
        self.close_button.clicked.connect(self.reject)
