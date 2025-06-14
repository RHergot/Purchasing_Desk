# Fichier: app/controllers/ao_list_controller.py (Version Assainie)

# Imports de librairies externes
from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QMessageBox
from sqlalchemy.orm import joinedload

# Imports de notre application
from app.database import get_db_session
from app.models.purchase_models import AppelOffre
from app.views.ao_detail_dialog import AoDetailDialog
from app.controllers.ao_detail_controller import AoDetailController

class AoListController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
        self.model = QStandardItemModel()
        self.view.table_view.setModel(self.model)
        
        self.view.refresh_button.clicked.connect(self.load_open_aos)
        self.view.open_ao_button.clicked.connect(self.open_ao_details)
        self.view.table_view.doubleClicked.connect(self.open_ao_details)

    def load_open_aos(self):
        print("Loading open RFQs...")
        self.model.clear()
        
        headers = ["RFQ ID", "RFQ Reference", "Title", "Linked Order ID", "Creator", "Creation Date", "Status"]
        self.model.setHorizontalHeaderLabels([self.view.tr(h) for h in headers])
        
        session = next(get_db_session())
        try:
            open_aos = session.query(AppelOffre).options(
                joinedload(AppelOffre.createur)
            ).filter(AppelOffre.statut == 'Ouvert').order_by(AppelOffre.date_creation.desc()).all()
            
            for ao in open_aos:
                id_item = QStandardItem(str(ao.id_ao))
                id_item.setData(ao.id_ao, Qt.UserRole)
                row = [
                    id_item, QStandardItem(ao.reference_ao), QStandardItem(ao.titre),
                    QStandardItem(str(ao.commande_id)),
                    QStandardItem(ao.createur.nom_complet if ao.createur else "N/A"),
                    QStandardItem(ao.date_creation.strftime("%Y-%m-%d %H:%M")),
                    QStandardItem(ao.statut)
                ]
                self.model.appendRow(row)
            
            print(f"Loaded {len(open_aos)} open RFQs.")
        finally:
            session.close()

        self.view.table_view.resizeColumnsToContents()

    def open_ao_details(self):
        selected_indexes = self.view.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self.view, self.tr("No Selection"), self.tr("Please select an RFQ to open."))
            return

        selected_row = selected_indexes[0].row()
        id_item = self.model.item(selected_row, 0)
        ao_id = id_item.data(Qt.UserRole)
        
        if ao_id is None:
            print("Error: Could not retrieve AO ID from selected row.")
            return

        print(f"Attempting to open dialog for AO ID: {ao_id}")
        
        # Instanciation de la boîte de dialogue
        dialog = AoDetailDialog(parent=self.view)
        # Instanciation de son contrôleur
        controller = AoDetailController(dialog_view=dialog, ao_id=ao_id)
        
        dialog.exec()