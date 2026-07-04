from PySide6.QtCore import QObject, Qt, QDate
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QMessageBox

from database import get_db_session
from app.models.purchase_models import Commande, LigneCommande
from app.models.shared_models import Fournisseur, Article

from decimal import Decimal


class OrdersKpiController(QObject):
    """
    Contrôleur pour la vue OrdersKpiView.
    - Récupère les données selon filtres
    - Calcule KPIs (nb commandes, total HT, panier moyen)
    - Alimente les tableaux Top fournisseurs / Top pièces
    """

    def __init__(self, view):
        super().__init__(view)
        self.view = view

        # Connexions signaux -> slots
        self.view.apply_button.clicked.connect(self.apply_filters)

        # Chargement initial
        self.populate_filters()
        self.load_data()

    # ------------------------- UI wiring -------------------------
    def populate_filters(self):
        """Remplit les combos Fournisseur et Pièce."""
        session = next(get_db_session())
        try:
            # Fournisseurs
            self.view.supplier_combo.blockSignals(True)
            # Conserve l'item 0 "Tous les fournisseurs"
            self.view.supplier_combo.clear()
            self.view.supplier_combo.addItem(self.view.tr("All suppliers"), None)
            for f in session.query(Fournisseur).order_by(Fournisseur.nom.asc()).all():
                self.view.supplier_combo.addItem(f.nom, f.id_fournisseur)
            self.view.supplier_combo.blockSignals(False)

            # Pièces
            self.view.piece_combo.blockSignals(True)
            self.view.piece_combo.clear()
            self.view.piece_combo.addItem(self.view.tr("All items"), None)
            for a in session.query(Article).order_by(Article.reference.asc()).all():
                self.view.piece_combo.addItem(f"{a.reference} - {a.designation}", a.id_piece)
            self.view.piece_combo.blockSignals(False)
        except Exception as e:
            print(f"ERROR populate_filters: {e}")
        finally:
            session.close()

    def apply_filters(self):
        self.load_data()

    # ------------------------- Data & KPIs -------------------------
    def _current_filters(self):
        start = self.view.start_date_edit.date().toPython()
        end = self.view.end_date_edit.date().toPython()
        supplier_id = self.view.supplier_combo.currentData()
        piece_id = self.view.piece_combo.currentData()
        return start, end, supplier_id, piece_id

    def load_data(self):
        """Charge les données et met à jour KPIs et tableaux."""
        start, end, supplier_id, piece_id = self._current_filters()

        session = next(get_db_session())
        try:
            q_cmd = session.query(Commande).filter(
                Commande.date_commande.isnot(None),
                Commande.date_commande >= start,
                Commande.date_commande <= end
            )
            if supplier_id:
                q_cmd = q_cmd.filter(Commande.fournisseur_id == supplier_id)

            commandes = q_cmd.all()
            nb_commandes = len(commandes)

            # Détail lignes pour Total HT et Top
            q_lignes = (
                session.query(LigneCommande)
                .join(Commande, LigneCommande.commande_id == Commande.id_commande)
                .filter(Commande.date_commande.isnot(None),
                        Commande.date_commande >= start,
                        Commande.date_commande <= end)
            )
            if supplier_id:
                q_lignes = q_lignes.filter(Commande.fournisseur_id == supplier_id)
            if piece_id:
                q_lignes = q_lignes.filter(LigneCommande.piece_id == piece_id)

            lignes = q_lignes.all()

            total_ht = Decimal("0")
            for lc in lignes:
                # On suppose présence de champs quantite_commandee et prix_unitaire
                qte = getattr(lc, 'quantite_commandee', 0) or 0
                pu = getattr(lc, 'prix_unitaire_ht', 0) or 0
                total_ht += Decimal(str(pu)) * Decimal(str(qte))

            panier_moyen = (total_ht / nb_commandes) if nb_commandes > 0 else Decimal("0")

            # KPIs
            self.view.orders_count_label.setText(self.view.tr(f"Orders: {nb_commandes}"))
            self.view.orders_total_ht_label.setText(self.view.tr(f"Total (excl. tax): {total_ht}"))
            self.view.orders_avg_basket_label.setText(self.view.tr(f"Average basket: {panier_moyen}"))

            # Top fournisseurs
            self._populate_top_suppliers(session, start, end, piece_id)
            # Top pièces
            self._populate_top_pieces(session, start, end, supplier_id)

        except Exception as e:
            print(f"ERROR load_data: {e}")
            QMessageBox.warning(self.view, self.view.tr("Error"), str(e))
        finally:
            session.close()

    def _populate_top_suppliers(self, session, start, end, piece_id):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels([self.view.tr("Supplier"), self.view.tr("Total (excl. tax)")])

        # Agrégation manuelle avec Python pour rester robuste (champs variables)
        totals_by_supplier = {}
        q = (
            session.query(LigneCommande, Commande, Fournisseur)
            .join(Commande, LigneCommande.commande_id == Commande.id_commande)
            .join(Fournisseur, Commande.fournisseur_id == Fournisseur.id_fournisseur)
            .filter(Commande.date_commande.isnot(None),
                    Commande.date_commande >= start,
                    Commande.date_commande <= end)
        )
        if piece_id:
            q = q.filter(LigneCommande.piece_id == piece_id)

        for lc, cmd, f in q.all():
            qte = getattr(lc, 'quantite_commandee', 0) or 0
            pu = getattr(lc, 'prix_unitaire_ht', 0) or 0
            amt = Decimal(str(pu)) * Decimal(str(qte))
            totals_by_supplier[f.nom] = totals_by_supplier.get(f.nom, Decimal("0")) + amt

        for name, total in sorted(totals_by_supplier.items(), key=lambda x: x[1], reverse=True)[:20]:
            model.appendRow([
                QStandardItem(name),
                QStandardItem(str(total))
            ])

        self.view.top_suppliers_table.setModel(model)
        self.view.top_suppliers_table.resizeColumnsToContents()

    def _populate_top_pieces(self, session, start, end, supplier_id):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels([self.view.tr("Reference"), self.view.tr("Designation"), self.view.tr("Qty"), self.view.tr("Total (excl. tax)")])

        totals_by_piece = {}
        q = (
            session.query(LigneCommande, Commande, Article)
            .join(Commande, LigneCommande.commande_id == Commande.id_commande)
            .join(Article, LigneCommande.piece_id == Article.id_piece)
            .filter(Commande.date_commande.isnot(None),
                    Commande.date_commande >= start,
                    Commande.date_commande <= end)
        )
        if supplier_id:
            q = q.filter(Commande.fournisseur_id == supplier_id)

        for lc, cmd, art in q.all():
            qte = getattr(lc, 'quantite_commandee', 0) or 0
            pu = getattr(lc, 'prix_unitaire_ht', 0) or 0
            amt = Decimal(str(pu)) * Decimal(str(qte))
            key = (art.reference, art.designation)
            if key not in totals_by_piece:
                totals_by_piece[key] = {"qte": 0, "total": Decimal("0")}
            totals_by_piece[key]["qte"] += qte
            totals_by_piece[key]["total"] += amt

        for (ref, des), agg in sorted(totals_by_piece.items(), key=lambda x: x[1]["total"], reverse=True)[:50]:
            model.appendRow([
                QStandardItem(str(ref)),
                QStandardItem(des or ""),
                QStandardItem(str(agg["qte"])),
                QStandardItem(str(agg["total"]))
            ])

        self.view.top_pieces_table.setModel(model)
        self.view.top_pieces_table.resizeColumnsToContents()
