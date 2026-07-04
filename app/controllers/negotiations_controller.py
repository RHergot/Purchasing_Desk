from PySide6.QtCore import QObject, Qt, QDate
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor
from PySide6.QtWidgets import QMessageBox
from sqlalchemy.orm import joinedload
import datetime # Si utilisé, sinon peut être enlevé

from database import get_db_session
from app.models.purchase_models import LigneCommande, Commande
from app.models.shared_models import Article, Fournisseur, PieceExtension, Machine

class NegotiationsController(QObject):
    def __init__(self, view):
        super().__init__(view)
        self.view = view
        self.model = QStandardItemModel()
        self.view.table_view.setModel(self.model)       
        
        # États des filtres et du tri
        self.current_sort_mode = "commande"
        self.current_supplier_filter_id = None
        self.current_piece_filter_ref = None
        self.current_machine_filter_id = None # Nouvel attribut pour le filtre machine
        # Nouveaux attributs pour les dates
        self.current_start_date_str = None
        self.current_end_date_str = None
        
        print(f"DEBUG INIT: Initial sort mode: {self.current_sort_mode}")
        
        # Connexion du bouton de tri
        if hasattr(self.view, 'toggle_sort_button') and self.view.toggle_sort_button is not None:
            self.view.toggle_sort_button.clicked.connect(self.toggle_sort_and_reload)
            print("DEBUG INIT: toggle_sort_button.clicked connected.")
        else:
            print("ERROR INIT: toggle_sort_button not found in view.")

        # Connexion du ComboBox de filtre fournisseur
        if hasattr(self.view, 'supplier_filter_combo') and self.view.supplier_filter_combo is not None:
            self.view.supplier_filter_combo.currentIndexChanged.connect(self.on_supplier_filter_changed)
            print("DEBUG INIT: supplier_filter_combo.currentIndexChanged connected.")
        else:
            print("ERROR INIT: supplier_filter_combo not found in view.")
            
        # Connexion du ComboBox de filtre pièce
        if hasattr(self.view, 'piece_filter_combo') and self.view.piece_filter_combo is not None:
            self.view.piece_filter_combo.currentIndexChanged.connect(self.on_piece_filter_changed)
            print("DEBUG INIT: piece_filter_combo.currentIndexChanged connected.")
        else:
            print("ERROR INIT: piece_filter_combo not found in view.")
        
         # Connecter le ComboBox de filtre machine
        if hasattr(self.view, 'machine_filter_combo') and self.view.machine_filter_combo is not None:
            self.view.machine_filter_combo.currentIndexChanged.connect(self.on_machine_filter_changed)
            print("DEBUG INIT: machine_filter_combo.currentIndexChanged connected.")
        else:
            print("ERROR INIT: machine_filter_combo not found or is None in view.")

         # Connecter les QDateEdit
        if hasattr(self.view, 'start_date_edit') and self.view.start_date_edit is not None:
            self.view.start_date_edit.dateChanged.connect(self.on_date_filter_changed)
            print("DEBUG INIT: start_date_edit.dateChanged connected.")
        else:
            print("ERROR INIT: start_date_edit not found in view.")
            
        if hasattr(self.view, 'end_date_edit') and self.view.end_date_edit is not None:
            self.view.end_date_edit.dateChanged.connect(self.on_date_filter_changed)
            print("DEBUG INIT: end_date_edit.dateChanged connected.")
        else:
            print("ERROR INIT: end_date_edit not found in view.")
            
        self.populate_all_filters() # Peupler tous les filtres une fois au démarrage
        self.load_negotiation_data()    # Chargement initial des données

    
    def on_date_filter_changed(self): # Peut être appelé par l'un ou l'autre QDateEdit
        """
        Called when the date filter (start or end) changes.
        Updates the current date filters and reloads data.
        """
        if not hasattr(self.view, 'start_date_edit') or not hasattr(self.view, 'end_date_edit'):
            return
        
        start_qdate = self.view.start_date_edit.date()
        end_qdate = self.view.end_date_edit.date()

        # S'assurer que la date de fin n'est pas avant la date de début
        if start_qdate > end_qdate:
            self.view.end_date_edit.setDate(start_qdate) # Ajuster la date de fin
            end_qdate = start_qdate
            # Ou afficher un message d'erreur et ne pas recharger

        self.current_start_date_str = start_qdate.toString("yyyy-MM-dd")
        self.current_end_date_str = end_qdate.toString("yyyy-MM-dd")
        
        print(f"DEBUG FILTER CHANGED: Date range set to: {self.current_start_date_str} - {self.current_end_date_str}")
        self.load_negotiation_data()
    
    def populate_all_filters(self):
        """Populates all filter ComboBoxes."""
        print("DEBUG POPULATE_ALL_FILTERS: Starting to populate all filters.")
        self.populate_supplier_filter_combo()
        self.populate_piece_filter_combo()
        self.populate_machine_filter_combo() # Appel de la nouvelle méthode
        # self.populate_machine_filter_combo() # À ajouter plus tard
        print("DEBUG POPULATE_ALL_FILTERS: Finished populating all filters.")

    def populate_supplier_filter_combo(self):
        if not hasattr(self.view, 'supplier_filter_combo'): return
        print("DEBUG POPULATE_SUPPLIER: Populating...")
        
        # Sauver la sélection actuelle pour essayer de la restaurer
        previous_selected_id = self.view.supplier_filter_combo.currentData()

        self.view.supplier_filter_combo.blockSignals(True)
        self.view.supplier_filter_combo.clear()
        self.view.supplier_filter_combo.addItem(self.view.tr("All Suppliers"), None)
        
        session = next(get_db_session())
        try:
            suppliers_in_orders = session.query(Fournisseur.id_fournisseur, Fournisseur.nom)\
                                        .join(Commande, Fournisseur.id_fournisseur == Commande.fournisseur_id)\
                                        .filter(Commande.statut.notin_(['Brouillon', 'Annulee']))\
                                        .distinct().order_by(Fournisseur.nom).all()
            for id_f, nom_f in suppliers_in_orders:
                self.view.supplier_filter_combo.addItem(nom_f, id_f)
            
            # Restaurer la sélection
            if previous_selected_id is not None:
                idx = self.view.supplier_filter_combo.findData(previous_selected_id)
                if idx != -1: self.view.supplier_filter_combo.setCurrentIndex(idx)

        except Exception as e: print(f"Error populating supplier filter: {e}")
        finally: 
            session.close()
            self.view.supplier_filter_combo.blockSignals(False)
        print("DEBUG POPULATE_SUPPLIER: Done.")
        pass

    def populate_piece_filter_combo(self):
        if not hasattr(self.view, 'piece_filter_combo'): return
        print("DEBUG POPULATE_PIECE: Populating...")

        previous_selected_ref = self.view.piece_filter_combo.currentData()

        self.view.piece_filter_combo.blockSignals(True)
        self.view.piece_filter_combo.clear()
        self.view.piece_filter_combo.addItem(self.view.tr("All Items"), None)
        
        session = next(get_db_session())
        try:
            item_refs = session.query(Article.reference).join(LigneCommande, Article.id_piece == LigneCommande.piece_id)\
                                .join(Commande, LigneCommande.commande_id == Commande.id_commande)\
                                .filter(Commande.statut.notin_(['Brouillon', 'Annulee']))\
                                .distinct().order_by(Article.reference).all()
            for ref_tuple in item_refs:
                self.view.piece_filter_combo.addItem(ref_tuple[0], ref_tuple[0])
            
            if previous_selected_ref is not None:
                idx = self.view.piece_filter_combo.findData(previous_selected_ref)
                if idx != -1: self.view.piece_filter_combo.setCurrentIndex(idx)

        except Exception as e: print(f"Error populating piece filter: {e}")
        finally: 
            session.close()
            self.view.piece_filter_combo.blockSignals(False)
        print("DEBUG POPULATE_PIECE: Done.")
        pass

    def populate_machine_filter_combo(self):
       
        if not hasattr(self.view, 'machine_filter_combo'):
            print("DEBUG POPULATE_MACHINE: View has no machine_filter_combo.")
            return

        print("DEBUG POPULATE_MACHINE: Populating machine filter...")
        current_selection_data = self.view.machine_filter_combo.currentData()
        
        self.view.machine_filter_combo.blockSignals(True)
        self.view.machine_filter_combo.clear()
        
        self.view.machine_filter_combo.addItem(self.view.tr("All Machines"), None)
        
        session = next(get_db_session())
        try:
            # Utiliser Machine.nom au lieu de Machine.nom_machine
            machines = session.query(Machine.id_machine, Machine.nom)\
                              .join(PieceExtension, Machine.id_machine == PieceExtension.machine_id)\
                              .join(Article, PieceExtension.id_piece == Article.id_piece)\
                              .join(LigneCommande, Article.id_piece == LigneCommande.piece_id)\
                              .join(Commande, LigneCommande.commande_id == Commande.id_commande)\
                              .filter(Commande.statut.notin_(['Brouillon', 'Annulee']))\
                              .distinct().order_by(Machine.nom).all() # Utiliser Machine.nom ici aussi
            
            for id_m, nom_m in machines:
                self.view.machine_filter_combo.addItem(nom_m, id_m)
            
            print(f"DEBUG POPULATE_MACHINE: Populated with {len(machines)} machines.")

            if current_selection_data is not None:
                index = self.view.machine_filter_combo.findData(current_selection_data)
                if index >= 0: self.view.machine_filter_combo.setCurrentIndex(index)
            
        except Exception as e:
            print(f"Error populating machine filter: {e}")
            import traceback; traceback.print_exc() # Garder pour voir d'autres erreurs potentielles
        finally:
            session.close()
            self.view.machine_filter_combo.blockSignals(False)
        print("DEBUG POPULATE_MACHINE: Done.")
        pass

    def on_supplier_filter_changed(self, index):
        if not hasattr(self.view, 'supplier_filter_combo'): return
        self.current_supplier_filter_id = self.view.supplier_filter_combo.itemData(index)
        print(f"DEBUG FILTER CHANGED: Supplier ID set to: {self.current_supplier_filter_id}")
        self.load_negotiation_data()
        pass

    def on_piece_filter_changed(self, index):
        if not hasattr(self.view, 'piece_filter_combo'): return
        self.current_piece_filter_ref = self.view.piece_filter_combo.itemData(index)
        print(f"DEBUG FILTER CHANGED: Piece Ref set to: {self.current_piece_filter_ref}")
        self.load_negotiation_data()
        pass

    def on_machine_filter_changed(self, index):
        if not hasattr(self.view, 'machine_filter_combo'): return
        self.current_machine_filter_id = self.view.machine_filter_combo.itemData(index)
        print(f"DEBUG FILTER CHANGED: Machine ID set to: {self.current_machine_filter_id}")
        self.load_negotiation_data()
        pass

    def toggle_sort_and_reload(self):
        print(f"--- METHOD: toggle_sort_and_reload CALLED ---")
        # ... (logique de toggle_sort_and_reload comme avant, inchangée)
        if self.current_sort_mode == "commande":
            self.current_sort_mode = "piece"
            self.view.toggle_sort_button.setText(self.view.tr("Sort by Purchase Order"))
        else: 
            self.current_sort_mode = "commande"
            self.view.toggle_sort_button.setText(self.view.tr("Sort by Item Reference"))
        self.load_negotiation_data()


    def load_negotiation_data(self):
        print(f"Loading negotiation data (Sort: {self.current_sort_mode}, Supplier: {self.current_supplier_filter_id}, Piece: {self.current_piece_filter_ref})...")
        self.model.clear()
        
        headers = [
            "PO Number", "Order Date", "Supplier", 
            "Item Ref.", "Item Name", "Machine",
            "Qty", "Reference Price (Unit)", "Negotiated Price (Unit)",
            "Unit Saving", "Total Saving for Line"
        ]
        self.model.setHorizontalHeaderLabels([self.view.tr(h) for h in headers])
        
        total_savings_all_lines = 0.0
        session = next(get_db_session())

        try:
            base_query = session.query(LigneCommande).join(LigneCommande.commande).options(
                joinedload(LigneCommande.piece).joinedload(Article.extension_info).joinedload(PieceExtension.machine),
                joinedload(LigneCommande.commande).joinedload(Commande.fournisseur)
            ).filter(
                Commande.statut.notin_(['Brouillon', 'Annulee'])
            )

            # Appliquer les filtres existants (fournisseur, pièce, machine)
            # ...
            
            # --- AJOUT DU FILTRE DATE ---
            # Uniquement si les dates sont définies et si votre colonne date_commande est au format YYYY-MM-DD
            if self.current_start_date_str and self.current_end_date_str:
                print(f"DEBUG LOAD: Applying date filter: {self.current_start_date_str} to {self.current_end_date_str}")
                # La comparaison textuelle fonctionne si le format est YYYY-MM-DD
                base_query = base_query.filter(Commande.date_commande >= self.current_start_date_str)
                base_query = base_query.filter(Commande.date_commande <= self.current_end_date_str)
            # --- FIN AJOUT FILTRE DATE ---
        
            # Appliquer les filtres
            if self.current_supplier_filter_id is not None:
                print(f"DEBUG LOAD: Applying supplier filter ID: {self.current_supplier_filter_id}")
                base_query = base_query.filter(Commande.fournisseur_id == self.current_supplier_filter_id)
            
            if self.current_piece_filter_ref is not None:
                print(f"DEBUG LOAD: Applying piece filter Ref: {self.current_piece_filter_ref}")
                base_query = base_query.join(LigneCommande.piece).filter(Article.reference == self.current_piece_filter_ref)

            if self.current_machine_filter_id is not None:
                print(f"DEBUG LOAD: Applying machine filter ID: {self.current_machine_filter_id}")
                
                # Pour filtrer sur PieceExtension.machine_id, nous devons nous assurer
                # que LigneCommande est jointe à Piece (Article), et Piece à PieceExtension.
                
                # Vérifier si la jointure avec Piece (Article) est déjà faite (par le filtre pièce ou le tri pièce)
                # Une façon simple de le savoir est de vérifier si 'Article' est déjà dans les entités jointes de la query.
                # Cependant, pour plus de robustesse, on peut simplement ajouter les jointures.
                # SQLAlchemy est généralement assez bon pour ne pas dupliquer les jointures si elles sont déjà là.
                
                base_query = base_query.join(LigneCommande.piece) # Assure la jointure LigneCommande -> Piece(Article)
                base_query = base_query.join(Article.extension_info) # Assure la jointure Piece(Article) -> PieceExtension
                
                # Maintenant on peut filtrer sur PieceExtension
                base_query = base_query.filter(PieceExtension.machine_id == self.current_machine_filter_id)
            # --- FIN MODIFICATION FILTRE ---

            # Appliquer le tri
            if self.current_sort_mode == "piece":
                print("DEBUG LOAD: Applying sort by Item Reference (piece) for GROUPING LOGIC")
                # S'assurer que la jointure avec Article (Piece) est faite si pas déjà par le filtre
                if self.current_machine_filter_id is None and self.current_piece_filter_ref is None:
                    # Si aucun filtre n'a encore joint avec Piece, on le fait pour le tri
                    ordered_lines = base_query.join(LigneCommande.piece).order_by(Article.reference, Commande.date_commande.desc()).all()
                else:
                    # La jointure avec Piece a déjà été faite par l'un des filtres
                    ordered_lines = base_query.order_by(Article.reference, Commande.date_commande.desc()).all()
                
                # ... (Logique de groupement et setSpan pour le mode "pièce" comme précédemment) ...
                current_piece_id_for_group = None
                piece_group_start_model_row = -1
                rows_in_current_model_group = 0
                for ligne in ordered_lines:
                    if not ligne.piece: continue
                    if ligne.piece.id_piece != current_piece_id_for_group:
                        if piece_group_start_model_row != -1 and rows_in_current_model_group > 0:
                            self.view.table_view.setSpan(piece_group_start_model_row, 3, rows_in_current_model_group, 1)
                            self.view.table_view.setSpan(piece_group_start_model_row, 4, rows_in_current_model_group, 1)
                            self.view.table_view.setSpan(piece_group_start_model_row, 5, rows_in_current_model_group, 1)
                        current_piece_id_for_group = ligne.piece.id_piece
                        piece_group_start_model_row = self.model.rowCount()
                        rows_in_current_model_group = 0
                        machine_name_group = "N/A"
                        if ligne.piece.extension_info and ligne.piece.extension_info.machine:
                            machine_name_group = ligne.piece.extension_info.machine.nom
                        master_row_items = [
                            QStandardItem(""), QStandardItem(""), QStandardItem(""),
                            QStandardItem(ligne.piece.reference), QStandardItem(ligne.piece.designation),
                            QStandardItem(machine_name_group), QStandardItem(""), QStandardItem(""),
                            QStandardItem(""), QStandardItem(""), QStandardItem("")
                        ]
                        for item in master_row_items[3:6]:
                            font = item.font(); font.setBold(True); item.setFont(font)
                            item.setBackground(QColor("#F0F0F0"))
                        self.model.appendRow(master_row_items)
                        rows_in_current_model_group += 1

                    reference_price_unit = float(ligne.piece.prix_achat_ht or 0) if ligne.piece.prix_achat_ht is not None else 0.0
                    negotiated_price_unit = float(ligne.prix_unitaire_ht or 0)
                    quantity = int(ligne.quantite_commandee or 0)
                    unit_saving = reference_price_unit - negotiated_price_unit
                    line_total_saving = unit_saving * quantity
                    total_savings_all_lines += line_total_saving
                    detail_row_items = [
                        QStandardItem(ligne.commande.numero_commande or str(ligne.commande.id_commande)),
                        QStandardItem(str(ligne.commande.date_commande)),
                        QStandardItem(ligne.commande.fournisseur.nom if ligne.commande.fournisseur else "N/A"),
                        QStandardItem(""), QStandardItem(""), QStandardItem(""),
                        QStandardItem(str(quantity)), QStandardItem(f"{reference_price_unit:.2f}"),
                        QStandardItem(f"{negotiated_price_unit:.2f}"), QStandardItem(f"{unit_saving:.2f}"),
                        QStandardItem(f"{line_total_saving:.2f}")
                    ]
                    if unit_saving > 0: detail_row_items[9].setForeground(QColor("green")); detail_row_items[10].setForeground(QColor("green"))
                    elif unit_saving < 0: detail_row_items[9].setForeground(QColor("red")); detail_row_items[10].setForeground(QColor("red"))
                    self.model.appendRow(detail_row_items)
                    rows_in_current_model_group += 1
                if piece_group_start_model_row != -1 and rows_in_current_model_group > 0:
                    self.view.table_view.setSpan(piece_group_start_model_row, 3, rows_in_current_model_group, 1)
                    self.view.table_view.setSpan(piece_group_start_model_row, 4, rows_in_current_model_group, 1)
                    self.view.table_view.setSpan(piece_group_start_model_row, 5, rows_in_current_model_group, 1)

            else: # Tri par 'commande'
                print("DEBUG LOAD: Applying sort by Purchase Order (commande)")
                ordered_lines = base_query.order_by(Commande.date_commande.desc(), LigneCommande.id_ligne).all()
                # ... (Copiez ici la logique de peuplement du mode "commande" comme avant)
                for ligne in ordered_lines:
                    if not ligne.piece: continue
                    machine_name = "N/A"
                    if ligne.piece.extension_info and ligne.piece.extension_info.machine:
                        machine_name = ligne.piece.extension_info.machine.nom
                    reference_price_unit = float(ligne.piece.prix_achat_ht or 0) if ligne.piece.prix_achat_ht is not None else 0.0
                    negotiated_price_unit = float(ligne.prix_unitaire_ht or 0)
                    quantity = int(ligne.quantite_commandee or 0)
                    unit_saving = reference_price_unit - negotiated_price_unit
                    line_total_saving = unit_saving * quantity
                    total_savings_all_lines += line_total_saving
                    row = [
                        QStandardItem(ligne.commande.numero_commande or str(ligne.commande.id_commande)),
                        QStandardItem(str(ligne.commande.date_commande)),
                        QStandardItem(ligne.commande.fournisseur.nom if ligne.commande.fournisseur else "N/A"),
                        QStandardItem(ligne.piece.reference), QStandardItem(ligne.piece.designation),
                        QStandardItem(machine_name), QStandardItem(str(quantity)),
                        QStandardItem(f"{reference_price_unit:.2f}"), QStandardItem(f"{negotiated_price_unit:.2f}"),
                        QStandardItem(f"{unit_saving:.2f}"), QStandardItem(f"{line_total_saving:.2f}")
                    ]
                    if unit_saving > 0: row[9].setForeground(QColor("green")); row[10].setForeground(QColor("green"))
                    elif unit_saving < 0: row[9].setForeground(QColor("red")); row[10].setForeground(QColor("red"))
                    self.model.appendRow(row)

            print(f"Model populated with {self.model.rowCount()} rows for display.")
            self.view.total_savings_value_label.setText(f"{total_savings_all_lines:.2f} EUR")

        except Exception as e:
            print(f"Error loading negotiation data: {e}")
            import traceback
            traceback.print_exc()
            self.view.total_savings_value_label.setText(self.view.tr("Error"))
        finally:
            session.close()

        self.view.table_view.resizeColumnsToContents()
        if self.current_sort_mode == "piece":
            self.view.table_view.setSortingEnabled(False)
            print("DEBUG LOAD: Table sorting disabled for 'piece' mode.")
        else:
            self.view.table_view.setSortingEnabled(True)
            self.view.table_view.sortByColumn(-1, Qt.AscendingOrder)
            print("DEBUG LOAD: Table sorting enabled for 'commande' mode and reset.")
        
        print("DEBUG LOAD: Table operations complete.")