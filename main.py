import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTabWidget
from PySide6.QtGui import QAction # Nécessaire pour QAction si non importé ailleurs

# Importer toutes nos vues et contrôleurs
from app.views.pr_view import PurchaseRequisitionView
from app.controllers.pr_controller import PurchaseRequisitionController
from app.views.ao_list_view import AoListView
from app.controllers.ao_list_controller import AoListController

# IMPORTS POUR LE NOUVEAU KPI NEGOCIATIONS
from app.views.negotiations_view import NegotiationsView
from app.controllers.negotiations_controller import NegotiationsController
from app.views.piece_list_view import PieceListView
from app.controllers.piece_list_controller import PieceListController
from app.views.orders_kpi_view import OrdersKpiView
from app.controllers.orders_kpi_controller import OrdersKpiController
from app.views.financial_kpi_view import FinancialKpiView
from app.controllers.financial_kpi_controller import FinancialKpiController

# IMPORT CORRECT POUR LA BASE DE DONNÉES
from database import engine

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("Purchasing Desk"))
        self.setGeometry(100, 100, 1280, 800)

        # Création de la barre de menu
        menubar = self.menuBar()
        
        # --- Menu File ---
        file_menu = menubar.addMenu(self.tr("&File"))
        exit_action = QAction(self.tr("&Exit"), self) # Utiliser QAction pour les icônes/raccourcis plus tard
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # --- Menu KPI ---
        kpi_menu = menubar.addMenu(self.tr("&KPI"))
        
        catalogue_menu = menubar.addMenu(self.tr("&Catalogue"))
        view_pieces_action = QAction(self.tr("View Pieces..."), self)
        view_pieces_action.triggered.connect(self.show_piece_catalogue)
        catalogue_menu.addAction(view_pieces_action)
        
        # Sous-menu Negociations
        negociations_action = QAction(self.tr("Negociations"), self)
        negociations_action.triggered.connect(self.show_negociations_kpi)
        kpi_menu.addAction(negociations_action)
        
        # Sous-menu Orders (placeholder)
        orders_action = QAction(self.tr("Orders"), self)
        orders_action.triggered.connect(self.show_orders_kpi)
        kpi_menu.addAction(orders_action)
        
        # Sous-menu Financial (placeholder)
        financial_action = QAction(self.tr("Financial"), self)
        financial_action.triggered.connect(self.show_financial_kpi)
        kpi_menu.addAction(financial_action)

        # --- Créer le widget d'onglets ---
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Onglet 1: Draft Orders
        self.pr_view = PurchaseRequisitionView()
        self.pr_controller = PurchaseRequisitionController(view=self.pr_view)
        self.tab_widget.addTab(self.pr_view, self.tr("Draft Orders"))

        # Onglet 2: Open RFQs
        self.ao_list_view = AoListView()
        self.ao_list_controller = AoListController(view=self.ao_list_view)
        self.tab_widget.addTab(self.ao_list_view, self.tr("Open RFQs"))
        
        # Rafraîchir les données quand on change d'onglet
        self.tab_widget.currentChanged.connect(self.refresh_current_tab)
        
        # Chargement initial des données pour le premier onglet
        if self.tab_widget.count() > 0: # S'assurer qu'il y a au moins un onglet
            self.refresh_current_tab(self.tab_widget.currentIndex())
    
    def show_piece_catalogue(self):
        try:
            if not hasattr(self, 'piece_catalogue_window_instance') or not self.piece_catalogue_window_instance.isVisible():
                self.piece_catalogue_window_instance = QMainWindow(self)
                self.piece_catalogue_window_instance.setWindowTitle(self.tr("Pieces Catalogue"))
                
                piece_list_view_widget = PieceListView()
                # Le contrôleur est créé avec la vue
                piece_list_controller = PieceListController(view=piece_list_view_widget)
                # Important de garder une référence au contrôleur pour éviter qu'il soit détruit
                self.piece_catalogue_window_instance.controller = piece_list_controller 
                
                self.piece_catalogue_window_instance.setCentralWidget(piece_list_view_widget)
                self.piece_catalogue_window_instance.setGeometry(120, 120, 1000, 700)
            
            self.piece_catalogue_window_instance.show()
            self.piece_catalogue_window_instance.activateWindow()
            self.piece_catalogue_window_instance.raise_()
            
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), f"Could not open Piece Catalogue window:\n{e}")
            import traceback
            traceback.print_exc()

    def refresh_current_tab(self, index):
        """
        Refreshes the data of the currently visible tab.
        """
        if index == 0: # Onglet Draft Orders
            print("Refreshing Draft Orders tab...")
            if hasattr(self, 'pr_controller'): # Vérifier si le contrôleur existe
                self.pr_controller.load_draft_orders()
        elif index == 1: # Onglet Open RFQs
            print("Refreshing Open RFQs tab...")
            if hasattr(self, 'ao_list_controller'): # Vérifier si le contrôleur existe
                self.ao_list_controller.load_open_aos()

    def show_negociations_kpi(self):
        """
        Shows the Negotiations KPI window.
        """
        try:
            # On stocke la référence dans self pour éviter que la fenêtre soit détruite
            # par le garbage collector si elle n'est pas modale et qu'on ne la garde pas en référence.
            # Cela permet aussi d'éviter d'ouvrir plusieurs fois la même fenêtre (ou de la réutiliser).
            if not hasattr(self, 'negotiations_window_instance') or not self.negotiations_window_instance.isVisible():
                self.negotiations_window_instance = QMainWindow(self) # Parenter à la fenêtre principale
                self.negotiations_window_instance.setWindowTitle(self.tr("Negotiation Savings KPI"))
                
                negotiations_view_widget = NegotiationsView() # C'est un QWidget
                # Le contrôleur est instancié avec la vue
                negotiations_controller = NegotiationsController(view=negotiations_view_widget)
                self.negotiations_window_instance.controller = negotiations_controller # Store controller to keep it alive
                
                self.negotiations_window_instance.setCentralWidget(negotiations_view_widget)
                self.negotiations_window_instance.setGeometry(150, 150, 1200, 800) # Position et taille
            
            self.negotiations_window_instance.show()
            self.negotiations_window_instance.activateWindow() # Mettre au premier plan
            self.negotiations_window_instance.raise_() # S'assurer qu'elle est visible
            
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), f"Could not open Negotiations KPI window:\n{e}")
            import traceback
            traceback.print_exc()
        
    def show_orders_kpi(self):
        """
        Affiche la fenêtre KPI des commandes (Orders).
        """
        try:
            if not hasattr(self, 'orders_window_instance') or not self.orders_window_instance.isVisible():
                self.orders_window_instance = QMainWindow(self)
                self.orders_window_instance.setWindowTitle(self.tr("Orders KPI"))

                orders_view_widget = OrdersKpiView()
                orders_controller = OrdersKpiController(view=orders_view_widget)
                self.orders_window_instance.controller = orders_controller

                self.orders_window_instance.setCentralWidget(orders_view_widget)
                self.orders_window_instance.setGeometry(160, 160, 1200, 800)

            self.orders_window_instance.show()
            self.orders_window_instance.activateWindow()
            self.orders_window_instance.raise_()

        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), f"Could not open Orders KPI window:\n{e}")
            import traceback
            traceback.print_exc()
        
    def show_financial_kpi(self):
        """
        Affiche la fenêtre KPI financière.
        """
        try:
            if not hasattr(self, 'financial_window_instance') or not self.financial_window_instance.isVisible():
                self.financial_window_instance = QMainWindow(self)
                self.financial_window_instance.setWindowTitle(self.tr("Financial KPI"))

                financial_view_widget = FinancialKpiView()
                financial_controller = FinancialKpiController(view=financial_view_widget)
                self.financial_window_instance.controller = financial_controller

                self.financial_window_instance.setCentralWidget(financial_view_widget)
                self.financial_window_instance.setGeometry(170, 170, 1200, 800)

            self.financial_window_instance.show()
            self.financial_window_instance.activateWindow()
            self.financial_window_instance.raise_()

        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), f"Could not open Financial KPI window:\n{e}")
            import traceback
            traceback.print_exc()

def main():
    """
    Main function to initialize and run the application.
    """
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling) # Pour une meilleure gestion des écrans HD
    app = QApplication(sys.argv)
    
    try:
        connection = engine.connect()
        connection.close()
        print("Database connection successful.")
    except Exception as e:
        QMessageBox.critical(None, "Database Error", f"Could not connect to database: {e}")
        return # Quitter si la connexion échoue
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    # Nécessaire pour Qt.AA_EnableHighDpiScaling si utilisé
    from PySide6.QtCore import Qt # S'assurer que Qt est importé avant QApplication
    main()