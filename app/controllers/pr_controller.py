# Fichier: app/controllers/pr_controller.py (Version de débogage)

# Imports nécessaires
import datetime
from PySide6.QtCore import QObject, Qt # Qt est nécessaire pour UserRole
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QStandardItemModel, QStandardItem
from sqlalchemy.orm import joinedload

# Imports de l'application
# Imports corrects
from database import get_db_session
from app.models.purchase_models import Commande, AppelOffre

class PurchaseRequisitionController(QObject):
    def __init__(self, view):
        super().__init__()
        print("Controller __init__ started.") # DEBUG
        self.view = view
        self.model = QStandardItemModel()
        self.view.table_view.setModel(self.model)
        
        # Le texte du bouton sera mis à jour ici
        self.view.create_po_button.setText(self.view.tr("Start Request for Quotation..."))
        
        # Connexion des signaux
        # On s'assure de connecter les bonnes fonctions
        self.view.refresh_button.clicked.connect(self.load_draft_orders)
        self.view.create_po_button.clicked.connect(self.start_request_for_quotation)
        
        print("Controller signals connected.") # DEBUG

    def load_draft_orders(self):
        print("Controller: load_draft_orders called.") # DEBUG
        self.model.clear()
        
        headers = ["ID", "Order Number", "Supplier", "Creator", "Order Date", "Status"]
        self.model.setHorizontalHeaderLabels([self.view.tr(h) for h in headers])
        
        session = next(get_db_session())
        try:
            draft_orders = session.query(Commande).options(
                joinedload(Commande.fournisseur),
                joinedload(Commande.createur)
            ).filter(Commande.statut == 'Brouillon').order_by(Commande.id_commande.desc()).all()
            
            for order in draft_orders:
                id_item = QStandardItem(str(order.id_commande))
                id_item.setData(order.id_commande, Qt.UserRole)

                row = [
                    id_item,
                    QStandardItem(order.numero_commande or "N/A"),
                    QStandardItem(order.fournisseur.nom if order.fournisseur else "N/A"),
                    QStandardItem(order.createur.nom_complet if order.createur else "N/A"),
                    QStandardItem(str(order.date_commande)),
                    QStandardItem(order.statut)
                ]
                self.model.appendRow(row)
            
            print(f"Controller: Loaded {len(draft_orders)} draft orders.")
        finally:
            session.close()

        self.view.table_view.resizeColumnsToContents()

    def start_request_for_quotation(self):
        """
        Initiates an RFQ process for the selected draft order.
        """
        print("Controller: start_request_for_quotation called!") # DEBUG

        # 1. Récupérer la ligne sélectionnée
        selected_indexes = self.view.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self.view, self.view.tr("No Selection"), self.view.tr("Please select a draft order to process."))
            return

        selected_row = selected_indexes[0].row()
        id_item = self.model.item(selected_row, 0)
        commande_id = id_item.data(Qt.UserRole)

        # 2. Demander confirmation
        reply = QMessageBox.question(self.view, self.view.tr("Confirmation"), 
                                     self.view.tr(f"Do you want to start a new Request for Quotation for order ID {commande_id}?"))
        if reply == QMessageBox.No:
            return

        session = next(get_db_session())
        try:
            # 3. Vérifier qu'un AO n'existe pas déjà pour cette commande
            commande = session.query(Commande).filter(Commande.id_commande == commande_id).one()
            existing_ao = session.query(AppelOffre).filter(AppelOffre.commande_id == commande_id).first()
            if existing_ao:
                QMessageBox.critical(self.view, self.view.tr("Error"), self.view.tr(f"An RFQ (ID: {existing_ao.id_ao}) already exists for this order."))
                session.close()
                return

            # 4. Créer le nouvel Appel d'Offres (AO)
            new_ao_ref = f"AO-{datetime.date.today().year}-{commande.id_commande:04d}"
            new_ao = AppelOffre(
                commande_id=commande.id_commande,
                reference_ao=new_ao_ref,
                titre=f"Request for Quotation for order {commande.numero_commande or commande_id}",
                createur_id=commande.createur_id,
            )
            session.add(new_ao)
            
            # 5. Mettre à jour le statut de la commande originale
            commande.statut = 'Validee'
            
            session.commit()
            
            QMessageBox.information(self.view, self.view.tr("Success"), 
                                    self.view.tr(f"Request for Quotation {new_ao_ref} has been created successfully."))

        except Exception as e:
            session.rollback()
            QMessageBox.critical(self.view, self.view.tr("Database Error"), str(e))
        finally:
            session.close()
            
        # 6. Rafraîchir la liste
        self.load_draft_orders()