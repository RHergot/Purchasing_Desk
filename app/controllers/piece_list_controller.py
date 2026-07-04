# Fichier: app/controllers/piece_list_controller.py (Logique de filtrage adaptée)

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QDialog
from sqlalchemy.orm import joinedload

from database import get_db_session
from app.models.shared_models import Article, Fournisseur, PieceExtension, Machine
from app.views.piece_filter_dialog import PieceFilterDialog # Importer la dialogue

class PieceListController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view # view est une instance de PieceListView
        self.model = QStandardItemModel()
        self.view.table_view.setModel(self.model) # On suppose que PieceListView a un self.table_view

        # Connecter le bouton de filtre de PieceListView
        if hasattr(self.view, 'filter_button'): # Supposons un self.filter_button dans PieceListView
            self.view.filter_button.clicked.connect(self.open_filter_dialog)
        
        # Filtres actifs
        self.active_filter_type = 'all'
        self.active_filter_value = None
        
        self.load_filtered_pieces() # Chargement initial (tout actif)

    def open_filter_dialog(self):
        dialog = PieceFilterDialog(self.view) # Parenter à la vue principale
        if dialog.exec() == QDialog.Accepted:
            filter_type, filter_value = dialog.get_selected_filter()
            self.active_filter_type = filter_type
            self.active_filter_value = filter_value
            print(f"Filters applied: Type={self.active_filter_type}, Value={self.active_filter_value}")
            self.load_filtered_pieces()
            # Mettre à jour le label des filtres actifs dans PieceListView
            if hasattr(self.view, 'active_filters_label'):
                self.update_active_filters_label()


    def update_active_filters_label(self): # Nouvelle fonction pour le label
        if not hasattr(self.view, 'active_filters_label'): return
        
        label_text = self.view.tr("Current Filter: ")
        if self.active_filter_type == 'all':
            label_text += self.view.tr("All Active Pieces")
        elif self.active_filter_type == 'stock_alert':
            label_text += self.view.tr("Stock Alert Items")
        elif self.active_filter_type == 'machine':
            # Il faut retrouver le nom de la machine à partir de son ID
            session = next(get_db_session())
            try:
                machine = session.query(Machine).filter_by(id_machine=self.active_filter_value).first()
                label_text += self.view.tr(f"Machine = {machine.nom if machine else 'Unknown'}")
            finally:
                session.close()
        # Ajouter des cas similaires pour fournisseur et catégorie
        # ...
        else:
            label_text += f"{self.active_filter_type.capitalize()} = {self.active_filter_value or 'Any'}"
        self.view.active_filters_label.setText(label_text)


    def load_filtered_pieces(self):
        print(f"Loading filtered pieces. Filter type: {self.active_filter_type}, Value: {self.active_filter_value}")
        self.model.clear()
        
        headers = ["Ref.", "Name", "Category", "Machine", "Pref. Supplier", "Unit Price", "Stock", "Alert Lvl", "Status"]
        self.model.setHorizontalHeaderLabels([self.view.tr(h) for h in headers])
        
        session = next(get_db_session())
        try:
            query = session.query(Article).options( # On requête directement les Articles (Pièces)
                joinedload(Article.fournisseur_default), # Pour le nom du fournisseur préféré
                joinedload(Article.extension_info).joinedload(PieceExtension.machine) # Pour le nom de la machine
            )
            
            # Filtre de base : statut actif
            query = query.filter(Article.statut == 'actif') # Ou le nom exact de votre statut actif

            # Dans app/controllers/piece_list_controller.py
# Dans la fonction load_filtered_pieces

            # Appliquer le filtre principal sélectionné
            if self.active_filter_type == 'machine' and self.active_filter_value is not None:
                query = query.join(Article.extension_info).filter(PieceExtension.machine_id == self.active_filter_value)
            elif self.active_filter_type == 'supplier' and self.active_filter_value is not None:
                query = query.filter(Article.fournisseur_id_default == self.active_filter_value)
            elif self.active_filter_type == 'category' and self.active_filter_value is not None:
                # Assurez-vous que active_filter_value est bien le nom de la catégorie ici
                query = query.filter(Article.categorie == self.active_filter_value)
            elif self.active_filter_type == 'stock_alert':
                query = query.filter(Article.stock_actuel <= Article.stock_alerte)
            # Si 'all' ou si filter_value est None pour un critère spécifique, aucun filtre principal supplémentaire.
            query = query.order_by(Article.reference) # Tri par défaut
            
            filtered_pieces = query.all()

            for piece in filtered_pieces:
                machine_name = "N/A"
                if piece.extension_info and piece.extension_info.machine:
                    machine_name = piece.extension_info.machine.nom
                
                supplier_name = "N/A"
                if piece.fournisseur_default:
                    supplier_name = piece.fournisseur_default.nom

                row = [
                    QStandardItem(piece.reference),
                    QStandardItem(piece.designation), # 'nom' dans votre table piece
                    QStandardItem(piece.categorie or ""),
                    QStandardItem(machine_name),
                    QStandardItem(supplier_name),
                    QStandardItem(f"{float(piece.prix_achat_ht):.2f}" if piece.prix_achat_ht is not None else "N/A"),
                    QStandardItem(str(piece.stock_actuel if piece.stock_actuel is not None else 0)),
                    QStandardItem(str(piece.stock_alerte if piece.stock_alerte is not None else 0)),
                    QStandardItem(piece.statut)
                ]
                self.model.appendRow(row)
            
            print(f"Loaded {len(filtered_pieces)} pieces matching criteria.")

        except Exception as e:
            print(f"Error loading filtered pieces: {e}")
            import traceback
            traceback.print_exc()
        finally:
            session.close()
        self.view.table_view.resizeColumnsToContents()
        if hasattr(self.view, 'active_filters_label'): self.update_active_filters_label() # Mettre à jour le label à la fin aussi