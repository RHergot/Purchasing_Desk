# Fichier: app/views/enter_offer_dialog.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                               QTableView, QDialogButtonBox, QGroupBox, QSpinBox,
                               QPlainTextEdit)

class EnterOfferDialog(QDialog):
    """
    Dialog to enter the pricing details from a supplier's offer.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Enter Supplier Offer"))
        self.setMinimumSize(700, 500)

        self.layout = QVBoxLayout(self)
        
        # --- General Offer Info ---
        info_group = QGroupBox(self.tr("General Offer Information"))
        form = QFormLayout(info_group)
        
        self.supplier_name_label = QLineEdit()
        self.supplier_name_label.setReadOnly(True)
        self.offer_ref_input = QLineEdit()
        self.delivery_days_input = QSpinBox()
        self.delivery_days_input.setRange(0, 365)
        
        form.addRow(self.tr("Supplier:"), self.supplier_name_label)
        form.addRow(self.tr("Supplier's Offer Ref:"), self.offer_ref_input)
        form.addRow(self.tr("Proposed Delivery (days):"), self.delivery_days_input)
        
        self.layout.addWidget(info_group)
        
        # --- Pricing Table ---
        pricing_group = QGroupBox(self.tr("Item Pricing"))
        pricing_layout = QVBoxLayout(pricing_group)
        
        self.pricing_table_view = QTableView()
        self.pricing_table_view.setAlternatingRowColors(True)
        
        pricing_layout.addWidget(self.pricing_table_view)
        self.layout.addWidget(pricing_group)

        # --- Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.layout.addWidget(self.button_box)
        
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)