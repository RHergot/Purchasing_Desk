import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTabWidget

# Importer toutes nos vues et contrôleurs
# Imports corrects
from app.views.pr_view import PurchaseRequisitionView
from app.controllers.pr_controller import PurchaseRequisitionController
from app.views.ao_list_view import AoListView
from app.controllers.ao_list_controller import AoListController
from app.database import engine

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("Purchasing Desk"))
        self.setGeometry(100, 100, 1280, 800)

        # Créer le widget d'onglets
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # --- Onglet 1: Draft Orders ---
        self.pr_view = PurchaseRequisitionView()
        self.pr_controller = PurchaseRequisitionController(view=self.pr_view)
        self.tab_widget.addTab(self.pr_view, self.tr("Draft Orders"))

        # --- Onglet 2: Open RFQs ---
        self.ao_list_view = AoListView()
        self.ao_list_controller = AoListController(view=self.ao_list_view)
        self.tab_widget.addTab(self.ao_list_view, self.tr("Open RFQs (Requests for Quotation)"))
        
        # Rafraîchir les données quand on change d'onglet
        self.tab_widget.currentChanged.connect(self.refresh_current_tab)
        
        # Chargement initial des données pour le premier onglet
        self.pr_controller.load_draft_orders()

    def refresh_current_tab(self, index):
        """
        Refreshes the data of the currently visible tab.
        """
        if index == 0: # Onglet Draft Orders
            print("Refreshing Draft Orders tab...")
            self.pr_controller.load_draft_orders()
        elif index == 1: # Onglet Open RFQs
            print("Refreshing Open RFQs tab...")
            self.ao_list_controller.load_open_aos()

# ... (La fonction main() reste la même que dans la version 'débogage')
def main():
    app = QApplication(sys.argv)
    
    try:
        from app.database import engine
        connection = engine.connect()
        connection.close()
        print("Database connection successful.")
    except Exception as e:
        QMessageBox.critical(None, "Database Error", f"Could not connect to database: {e}")
        return
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()