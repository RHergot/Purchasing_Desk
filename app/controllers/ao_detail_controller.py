# Fichier: app/controllers/ao_detail_controller.py

# Fichier: app/controllers/ao_detail_controller.py (Version Corrigée)

from PySide6.QtCore import QObject, QStringListModel, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QMessageBox, QDialog  # Correction ici
from PySide6.QtGui import QColor
from sqlalchemy.orm import joinedload
import datetime

from database import get_db_session
from app.models.purchase_models import OffreRecue, OffreRecueLigne, Commande, LigneCommande, AppelOffre, AoFournisseurConsulte
from app.models.shared_models import Fournisseur, Article
from app.views.select_supplier_dialog import SelectSupplierDialog
from app.views.enter_offer_dialog import EnterOfferDialog
from app.utils.pdf_generator import generate_purchase_order_pdf, generate_rfq_pdf

class AoDetailController(QObject):
    def __init__(self, dialog_view, ao_id):
        super().__init__()
        self.view = dialog_view
        self.ao_id = ao_id
        
        self.suppliers_model = QStandardItemModel()
        self.comparison_model = QStandardItemModel()
        
        self.view.suppliers_table_view.setModel(self.suppliers_model)
        self.view.comparison_table_view.setModel(self.comparison_model)
        
        self.view.add_supplier_button.clicked.connect(self.add_supplier_to_rfq)
        self.view.enter_offer_button.clicked.connect(self.enter_supplier_offer)
        self.view.generate_rfq_pdf_button.clicked.connect(self.generate_generic_rfq_pdf)
                
        print("DEBUG (Detail): Detail controller signals connected.")

        self.view.generate_supplier_rfq_pdf_button.clicked.connect(self.generate_specific_supplier_rfq_pdf)
        self.view.suppliers_table_view.selectionModel().selectionChanged.connect(self.on_supplier_selection_changed)        
        self.view.comparison_table_view.doubleClicked.connect(self.on_price_selected)
        self.view.button_box.accepted.connect(self.finalize_orders)
        # Dictionnaire pour garder en mémoire les sélections
        # Format: { num_ligne: num_colonne_selectionnee }
        self.selected_offers = {}
        
        self.load_ao_details()
    
    def load_ao_details(self):
        self.load_general_info()
        self.load_consulted_suppliers()
        self.build_comparison_table()

    def load_general_info(self):
        session = next(get_db_session())
        try:
            ao = session.query(AppelOffre).filter(AppelOffre.id_ao == self.ao_id).one()
            self.view.ref_ao_label.setText(ao.reference_ao)
            self.view.titre_label.setText(ao.titre)
        finally:
            session.close()

    def load_consulted_suppliers(self):
        print("Loading consulted suppliers...")
        self.suppliers_model.clear()
        headers = ["Supplier Name", "Has Replied?"]
        self.suppliers_model.setHorizontalHeaderLabels([self.view.tr(h) for h in headers])
        
        session = next(get_db_session())
        try:
            consulted = session.query(AoFournisseurConsulte).options(
                joinedload(AoFournisseurConsulte.fournisseur)
            ).filter(AoFournisseurConsulte.ao_id == self.ao_id).all()

            for entry in consulted:
                row = [
                    QStandardItem(entry.fournisseur.nom),
                    QStandardItem("Yes" if entry.a_repondu else "No")
                ]
                self.suppliers_model.appendRow(row)
        finally:
            session.close()

    
    def add_supplier_to_rfq(self):
        session = next(get_db_session())
        try:
            all_suppliers = session.query(Fournisseur).order_by(Fournisseur.nom).all()
            if not all_suppliers:
                QMessageBox.warning(self.view, self.tr("No Suppliers"), self.tr("No suppliers found in the database."))
                return

            dialog = SelectSupplierDialog(self.view)
            
            self.supplier_objects = {f.nom: f for f in all_suppliers}
            supplier_names = list(self.supplier_objects.keys())
            
            list_model = QStringListModel(supplier_names)
            dialog.list_view.setModel(list_model)

            if dialog.exec() == QDialog.Accepted:
                selected_indexes = dialog.list_view.selectedIndexes()
                if not selected_indexes:
                    return
                
                selected_name = selected_indexes[0].data()
                selected_supplier = self.supplier_objects[selected_name]
                
                existing = session.query(AoFournisseurConsulte).filter_by(ao_id=self.ao_id, fournisseur_id=selected_supplier.id_fournisseur).first()
                if existing:
                    QMessageBox.information(self.view, self.tr("Already Added"), self.tr("This supplier is already in the list for this RFQ."))
                    return

                new_consulted = AoFournisseurConsulte(
                    ao_id=self.ao_id,
                    fournisseur_id=selected_supplier.id_fournisseur
                )
                session.add(new_consulted)
                session.commit()
                
                print(f"Added supplier '{selected_supplier.nom}' to RFQ ID {self.ao_id}")
                
                self.load_consulted_suppliers()

        except Exception as e:
            session.rollback()
            QMessageBox.critical(self.view, self.tr("Database Error"), str(e))
        finally:
            session.close()

    def enter_supplier_offer(self):
        """
        Opens a dialog to enter or edit a supplier's offer.
        """
        # 1. Récupérer le fournisseur sélectionné
        selected_indexes = self.view.suppliers_table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self.view, self.tr("No Supplier Selected"), self.tr("Please select a supplier from the list to enter their offer."))
            return

        selected_row = selected_indexes[0].row()
        supplier_name = self.suppliers_model.item(selected_row, 0).text()
        
        # 2. Ouvrir la dialogue de saisie
        dialog = EnterOfferDialog(self.view)
        dialog.supplier_name_label.setText(supplier_name)
        
        # 3. Pré-remplir la dialogue avec les données existantes (si elles existent)
        # et peupler le tableau des pièces à chiffrer.
        self.populate_offer_dialog(dialog, supplier_name)

        # 4. Si l'utilisateur clique sur "Save"
        if dialog.exec() == QDialog.Accepted:
            self.save_supplier_offer(dialog, supplier_name)

    def populate_offer_dialog(self, dialog, supplier_name):
        """
        Fills the 'Enter Offer' dialog with the list of items to price
        and any existing offer data.
        """
        session = next(get_db_session())
        try:
            # Récupérer l'ID du fournisseur et de la commande
            supplier = session.query(Fournisseur).filter_by(nom=supplier_name).one()
            ao = session.query(AppelOffre).filter_by(id_ao=self.ao_id).one()
            
            # Charger les pièces de la commande originale
            commande = session.query(Commande).options(
                joinedload(Commande.lignes).joinedload(LigneCommande.piece)
            ).filter_by(id_commande=ao.commande_id).one()

            # Créer le modèle pour le tableau des prix
            pricing_model = QStandardItemModel()
            dialog.pricing_table_view.setModel(pricing_model)
            headers = ["Item Ref.", "Designation", "Qty", "Unit Price (€)"]
            pricing_model.setHorizontalHeaderLabels([dialog.tr(h) for h in headers])

            # Remplir le tableau avec les pièces
            for ligne_cmd in commande.lignes:
                piece_id_item = QStandardItem(str(ligne_cmd.piece_id))
                ref_item = QStandardItem(ligne_cmd.piece.reference)
                ref_item.setEditable(False)
                design_item = QStandardItem(ligne_cmd.piece.designation)
                design_item.setEditable(False)
                qty_item = QStandardItem(str(ligne_cmd.quantite_commandee))
                qty_item.setEditable(False)
                
                # Le champ du prix est éditable
                price_item = QStandardItem("0.00") 
                
                # On stocke l'ID de la pièce pour le retrouver facilement
                price_item.setData(ligne_cmd.piece_id, Qt.UserRole)

                pricing_model.appendRow([ref_item, design_item, qty_item, price_item])

        finally:
            session.close()

    def save_supplier_offer(self, dialog, supplier_name):
        """
        Saves the entered offer data into the database.
        """
        session = next(get_db_session())
        try:
            supplier = session.query(Fournisseur).filter_by(nom=supplier_name).one()

            # 1. Créer ou récupérer l'objet OffreRecue
            offre = session.query(OffreRecue).filter_by(ao_id=self.ao_id, fournisseur_id=supplier.id_fournisseur).first()
            if not offre:
                offre = OffreRecue(ao_id=self.ao_id, fournisseur_id=supplier.id_fournisseur)
                session.add(offre)
            
            # 2. Mettre à jour les infos générales de l'offre
            offre.reference_offre_fournisseur = dialog.offer_ref_input.text()
            offre.delai_livraison_propose_j = dialog.delivery_days_input.value()
            
            # 3. Parcourir le tableau pour sauvegarder chaque ligne de prix
            pricing_model = dialog.pricing_table_view.model()
            for row in range(pricing_model.rowCount()):
                price_item = pricing_model.item(row, 3)
                piece_id = price_item.data(Qt.UserRole)
                price_value = float(price_item.text().replace(',', '.'))

                # Créer ou récupérer la ligne d'offre
                offre_ligne = session.query(OffreRecueLigne).filter_by(offre_id=offre.id_offre, piece_id=piece_id).first()
                if not offre_ligne:
                     # S'assurer que l'offre a un ID avant de lier la ligne
                    session.flush() # Attribue un ID à la nouvelle 'offre'
                    offre_ligne = OffreRecueLigne(offre_id=offre.id_offre, piece_id=piece_id)
                    session.add(offre_ligne)
                
                offre_ligne.prix_unitaire_ht_propose = price_value
            
            # 4. Mettre à jour le statut du fournisseur consulté
            consulted_entry = session.query(AoFournisseurConsulte).filter_by(ao_id=self.ao_id, fournisseur_id=supplier.id_fournisseur).one()
            consulted_entry.a_repondu = True

            session.commit()
            QMessageBox.information(self.view, self.tr("Success"), self.tr("Supplier offer has been saved successfully."))

        except Exception as e:
            session.rollback()
            QMessageBox.critical(self.view, self.tr("Save Error"), f"An error occurred: {e}")
        finally:
            session.close()
            
        # Rafraîchir les vues pour montrer les changements
        self.load_consulted_suppliers()
        self.build_comparison_table() # <--- L'AJOUT IMPORTANT EST ICI
        # Plus tard, on rafraîchira le tableau comparatif
        # self.build_comparison_table()

    def on_price_selected(self, index):
        """
        Slot called when a user double-clicks a cell in the comparison table.
        """
        row = index.row()
        col = index.column()

        # Ignorer les clics sur les colonnes d'information (Item Ref, Designation)
        if col < 2: 
            return

        # Mettre à jour la sélection pour cette ligne
        self.selected_offers[row] = col
        print(f"DEBUG: Row {row} selection changed to column {col}")

        # Rafraîchir l'affichage pour montrer la nouvelle sélection
        self.refresh_comparison_table_highlighting()

    def refresh_comparison_table_highlighting(self):
        """
        Redraws the background colors of the comparison table based on selections.
        """
        model = self.view.comparison_table_view.model()
        for r in range(model.rowCount()):
            # Trouver le prix le plus bas pour cette ligne
            prices = []
            for c in range(2, model.columnCount()):
                item = model.item(r, c)
                try:
                    price = float(item.text())
                    prices.append(price)
                except (ValueError, TypeError):
                    prices.append(float('inf'))
            min_price = min(prices) if prices else None
            
            # Appliquer les couleurs
            for c in range(2, model.columnCount()):
                item = model.item(r, c)
                # Couleur de la sélection (bleu)
                if self.selected_offers.get(r) == c:
                    item.setBackground(QColor("lightblue"))
                # Couleur du prix le plus bas (vert)
                elif prices[c-2] == min_price:
                    item.setBackground(QColor("lightgreen"))
                # Pas de couleur
                else:
                    item.setBackground(QColor("white"))

    def build_comparison_table(self):
        print("DEBUG: build_comparison_table STARTING") # <-- PRINT 1
        self.comparison_model.clear()
        
        session = next(get_db_session())
        try:
            print("DEBUG: build_comparison_table - Session obtained") # <-- PRINT 2
            ao = session.query(AppelOffre).filter_by(id_ao=self.ao_id).one()
            commande = session.query(Commande).options(
                joinedload(Commande.lignes).joinedload(LigneCommande.piece)
            ).filter_by(id_commande=ao.commande_id).one()
            
            items_to_quote = commande.lignes
            if not items_to_quote:
                print("DEBUG: build_comparison_table - No items to quote. Returning.") # <-- PRINT 3
                return

            print(f"DEBUG: build_comparison_table - Found {len(items_to_quote)} items to quote.") # <-- PRINT 4

            offers = session.query(OffreRecue).options(
                joinedload(OffreRecue.fournisseur),
                joinedload(OffreRecue.lignes_offre)
            ).filter_by(ao_id=self.ao_id).all()
            
            print(f"DEBUG: build_comparison_table - Found {len(offers)} offers received.") # <-- PRINT 5

            headers = ["Item Ref.", "Designation"]
            supplier_columns = {}
            if offers: # Vérifier si on a des offres avant d'essayer d'accéder à offer.fournisseur
                supplier_columns = {offer.fournisseur.id_fournisseur: offer.fournisseur.nom for offer in offers}
            
            headers.extend(supplier_columns.values())
            self.view.comparison_table_view.model().setHorizontalHeaderLabels(headers)
            print(f"DEBUG: build_comparison_table - Headers set: {headers}") # <-- PRINT 6
            
            price_map = {}
            for offer in offers:
                for line in offer.lignes_offre:
                    if line.piece_id not in price_map:
                        price_map[line.piece_id] = {}
                    price_map[line.piece_id][offer.fournisseur_id] = line.prix_unitaire_ht_propose
            
            print(f"DEBUG: build_comparison_table - Price map built: {price_map}") # <-- PRINT 7

            for item in items_to_quote:
                piece = item.piece
                row_data = [
                    QStandardItem(piece.reference),
                    QStandardItem(piece.designation)
                ]
                
                prices_for_item = price_map.get(piece.id_piece, {}).values()
                min_price = min(prices_for_item) if prices_for_item else None
                
                for supplier_id in supplier_columns.keys():
                    price = price_map.get(piece.id_piece, {}).get(supplier_id)
                    price_str = f"{price:.2f}" if price is not None else "N/A"
                    price_item = QStandardItem(price_str)
                    row_data.append(price_item)
                
                self.comparison_model.appendRow(row_data)
            
            print("DEBUG: build_comparison_table - Rows appended to model.") # <-- PRINT 8
            self.view.comparison_table_view.resizeColumnsToContents()
            self.refresh_comparison_table_highlighting() # S'assurer que ça s'exécute
            print("DEBUG: build_comparison_table - Highlighting refreshed.") # <-- PRINT 9

        except Exception as e:
            print(f"ERROR in build_comparison_table: {e}") # <-- PRINT D'ERREUR
            import traceback
            traceback.print_exc() # Imprime le traceback complet
        finally:
            session.close()
            print("DEBUG: build_comparison_table - Session closed.") # <-- PRINT 10

    def finalize_orders(self):
        print("DEBUG (Finalize): finalize_orders STARTING") # <-- PRINT 1

        if not self.selected_offers:
            print("DEBUG (Finalize): No offers selected. Aborting.") # <-- PRINT 2
            QMessageBox.warning(self.view, "No Selection", "Please select at least one offer by double-clicking on a price.")
            return

        print(f"DEBUG (Finalize): Selected offers: {self.selected_offers}") # <-- PRINT 3

        supplier_baskets = {}
        model = self.view.comparison_table_view.model()
        
        supplier_ids_by_col = {}
        for col in range(2, model.columnCount()):
            header_text = model.horizontalHeaderItem(col).text()
            supplier_ids_by_col[col] = header_text
        
        print(f"DEBUG (Finalize): Supplier IDs by column: {supplier_ids_by_col}") # <-- PRINT 4

        session = next(get_db_session())
        try:
            print("DEBUG (Finalize): Session obtained.") # <-- PRINT 5
            ao = session.query(AppelOffre).filter_by(id_ao=self.ao_id).one() # S'assurer que ao est défini
            print(f"DEBUG (Finalize): Current AO ID: {ao.id_ao}, Original CMD ID: {ao.commande_id}") # <-- PRINT 5.1

            for row, col in self.selected_offers.items():
                supplier_name = supplier_ids_by_col[col]
                print(f"DEBUG (Finalize): Processing row {row}, col {col}, supplier_name: {supplier_name}") # <-- PRINT 6
                
                supplier = session.query(Fournisseur).filter_by(nom=supplier_name).one()
                print(f"DEBUG (Finalize): Found supplier ID: {supplier.id_fournisseur}") # <-- PRINT 7
                
                piece_ref = model.item(row, 0).text()
                piece = session.query(Article).filter_by(reference=piece_ref).one()
                print(f"DEBUG (Finalize): Found piece ID: {piece.id_piece}, Ref: {piece_ref}") # <-- PRINT 8
                
                # Récupérer la quantité depuis la commande originale
                # Utiliser ao.commande_id qui est déjà chargé
                ligne_cmd = session.query(LigneCommande).filter_by(commande_id=ao.commande_id, piece_id=piece.id_piece).one()
                quantity = ligne_cmd.quantite_commandee
                print(f"DEBUG (Finalize): Quantity: {quantity}") # <-- PRINT 9

                price = float(model.item(row, col).text())
                print(f"DEBUG (Finalize): Price: {price}") # <-- PRINT 10
                
                if supplier.id_fournisseur not in supplier_baskets:
                    supplier_baskets[supplier.id_fournisseur] = []
                
                supplier_baskets[supplier.id_fournisseur].append( (piece.id_piece, quantity, price) )
            
            print(f"DEBUG (Finalize): Supplier baskets built: {supplier_baskets}") # <-- PRINT 11

            created_orders_refs = []
            if not supplier_baskets:
                print("DEBUG (Finalize): No supplier baskets created. Nothing to commit.") # <-- PRINT 11.1
                QMessageBox.information(self.view, "No Action", "No valid offers were selected to create orders.")
                return


            for supplier_id, items in supplier_baskets.items():
                total_ht = sum(qty * price for _, qty, price in items)
                print(f"DEBUG (Finalize): Creating order for supplier ID {supplier_id}, total HT: {total_ht}") # <-- PRINT 12
                
                new_order_ref = f"BC-{datetime.date.today().year}-{self.ao_id}-{supplier_id}"
                
                new_commande = Commande(
                    numero_commande=new_order_ref,
                    fournisseur_id=supplier_id,
                    createur_id=ao.createur_id,
                    date_commande=str(datetime.date.today()),
                    statut='Envoyee',
                    total_ht=total_ht
                )
                session.add(new_commande)
                session.flush() 
                print(f"DEBUG (Finalize): New order {new_order_ref} (ID: {new_commande.id_commande}) added.") # <-- PRINT 13

                for piece_id, qty, price in items:
                    new_ligne = LigneCommande(
                        commande_id=new_commande.id_commande,
                        piece_id=piece_id,
                        quantite_commandee=qty,
                        prix_unitaire_ht=price
                    )
                    session.add(new_ligne)
                print(f"DEBUG (Finalize): Lines added for order {new_order_ref}.") # <-- PRINT 14
                
                created_orders_refs.append(new_order_ref)

            original_commande = session.query(Commande).filter_by(id_commande=ao.commande_id).one()
            original_commande.statut = 'Annulee'
            print(f"DEBUG (Finalize): Original command {original_commande.id_commande} status set to Annulee.") # <-- PRINT 15
            
            ao_to_close = session.query(AppelOffre).filter_by(id_ao=self.ao_id).one()
            ao_to_close.statut = 'Clos'
            print(f"DEBUG (Finalize): AO {ao_to_close.id_ao} status set to Clos.") # <-- PRINT 16
            
            session.commit()
            print("DEBUG (Finalize): Session committed.") # <-- PRINT 17

            QMessageBox.information(self.view, "Success", f"Process complete!\nCreated new purchase orders:\n" + "\n".join(created_orders_refs))
            
            self.view.accept()

        except Exception as e:
            session.rollback()
            print(f"ERROR in finalize_orders: {e}") # <-- PRINT D'ERREUR
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self.view, "Error during finalization", str(e))
        
        finally:
            session.close()
            print("DEBUG (Finalize): Session closed.") # <-- PRINT 18

        try:
            # ... (logique existante pour créer les commandes) ...
            session.commit()
            print("DEBUG (Finalize): Session committed.")

            # --- NOUVELLE PARTIE : GÉNÉRATION DES PDFS ---
            if created_orders_refs:
                msg = f"Process complete!\nCreated new purchase orders:\n" + "\n".join(created_orders_refs)
                msg += "\n\nDo you want to generate the PDF for these orders?"
                
                reply = QMessageBox.question(self.view, "Success & PDF Generation", msg,
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                
                if reply == QMessageBox.Yes:
                    # Récupérer les ID des nouvelles commandes créées
                    newly_created_orders_ids = []
                    for ref in created_orders_refs:
                        # On suppose que la référence est unique et permet de retrouver l'ID
                        # Ceci est un peu fragile, il serait mieux de stocker les ID directement
                        new_cmd = session.query(Commande).filter_by(numero_commande=ref).first()
                        if new_cmd:
                            newly_created_orders_ids.append(new_cmd.id_commande)
                    
                    for cmd_id in newly_created_orders_ids:
                        generate_purchase_order_pdf(cmd_id, parent_widget=self.view)
            else:
                 QMessageBox.information(self.view, "Process Complete", "No new orders were created (already processed or no selection).")
            # --- FIN DE LA NOUVELLE PARTIE ---
            
            self.view.accept() # Ferme la fenêtre de détail

        except Exception as e:
            session.rollback()
            print(f"ERROR in finalize_orders: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self.view, "Error during finalization", str(e))
        finally:
            session.close()
            print("DEBUG (Finalize): Session closed.")
            # Rafraîchir les listes dans la fenêtre principale après la fermeture du dialogue
            # On pourrait le faire via un signal émis par AoDetailDialog.
            # Pour l'instant, le rafraîchissement se fait au changement d'onglet.

    def generate_generic_rfq_pdf(self):
        """
        Generates a generic RFQ PDF (not addressed to a specific supplier).
        """
        if self.ao_id:
            generate_rfq_pdf(self.ao_id, parent_widget=self.view)
        else:
            QMessageBox.warning(self.view, "Error", "No RFQ loaded to generate PDF.")

    def on_supplier_selection_changed(self, selected, deselected):
        """
        Activates or deactivates buttons based on supplier selection.
        """
        has_selection = bool(self.view.suppliers_table_view.selectionModel().selectedRows())
        self.view.generate_supplier_rfq_pdf_button.setEnabled(has_selection)
        self.view.enter_offer_button.setEnabled(has_selection)

    # ... (garder load_open_aos, open_ao_details, etc. si elles sont dans ce fichier, sinon c'est bon)
    # ... (garder load_ao_details, load_general_info, load_consulted_suppliers, build_comparison_table)
    # ... (garder add_supplier_to_rfq, enter_supplier_offer, populate_offer_dialog, save_supplier_offer)
    # ... (garder finalize_orders, on_price_selected, refresh_comparison_table_highlighting)


    # --- NOUVELLE MÉTHODE SLOT ---
    def generate_specific_supplier_rfq_pdf(self):
        """
        Generates an RFQ PDF personalized for the selected supplier.
        """
        selected_indexes = self.view.suppliers_table_view.selectionModel().selectedRows()
        if not selected_indexes:
            # Ce cas ne devrait pas arriver si le bouton est correctement désactivé
            QMessageBox.warning(self.view, self.tr("No Supplier Selected"), self.tr("Please select a supplier."))
            return

        selected_row = selected_indexes[0].row()
        # Il faut stocker l'ID du fournisseur dans le modèle pour le récupérer facilement
        # Pour l'instant, on récupère le nom et on refait une requête, ce n'est pas optimal
        # On améliorera ça plus tard en stockant l'ID dans Qt.UserRole comme pour les autres tables
        
        supplier_name_item = self.suppliers_model.item(selected_row, 0)
        supplier_name = supplier_name_item.text()

        session = next(get_db_session())
        try:
            supplier = session.query(Fournisseur).filter_by(nom=supplier_name).one_or_none()
            if supplier and self.ao_id:
                print(f"Generating PDF for RFQ {self.ao_id} and Supplier {supplier.nom} (ID: {supplier.id_fournisseur})")
                
                # Mettre à jour la date d'envoi pour ce fournisseur (traçabilité)
                consulted_entry = session.query(AoFournisseurConsulte).filter_by(
                    ao_id=self.ao_id, 
                    fournisseur_id=supplier.id_fournisseur
                ).first()
                if consulted_entry:
                    consulted_entry.date_envoi = datetime.datetime.now() # Utiliser datetime
                    session.commit()
                    print(f"Updated date_envoi for supplier {supplier.nom} on RFQ {self.ao_id}")
                
                generate_rfq_pdf(self.ao_id, supplier.id_fournisseur, parent_widget=self.view)
            else:
                QMessageBox.warning(self.view, "Error", f"Could not find supplier: {supplier_name}")
        except Exception as e:
            session.rollback() # Rollback en cas d'erreur avant le commit de date_envoi
            QMessageBox.critical(self.view, "Error", f"An error occurred: {e}")
        finally:
            session.close()
