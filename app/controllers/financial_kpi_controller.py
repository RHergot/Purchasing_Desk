from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QMessageBox
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from database import get_db_session
from app.models.purchase_models import AppelOffre, Commande, LigneCommande, OffreRecue, OffreRecueLigne
from app.models.shared_models import Fournisseur, Article

from decimal import Decimal
from collections import defaultdict


class FinancialKpiController(QObject):
    """
    Contrôleur KPI financier.
    - Calcule Spend total, Savings (option A: moyenne des offres vs prix sélectionné), Taux de savings
    - Table Savings par AO
    - Table tendance prix moyen (placeholder: prix moyen par pièce sur la période)
    """

    def __init__(self, view):
        super().__init__(view)
        self.view = view
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(300)
        self._debounce_timer.timeout.connect(self.load_data)

        self.view.apply_button.clicked.connect(self.apply_filters)

        self.populate_filters()
        self.load_data()

    # ------------------------- UI wiring -------------------------
    def populate_filters(self):
        session = next(get_db_session())
        try:
            # Fournisseurs
            self.view.supplier_combo.blockSignals(True)
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
            print(f"ERROR populate_filters (financial): {e}")
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
        start, end, supplier_id, piece_id = self._current_filters()
        session = next(get_db_session())
        try:
            # Spend total = somme des montants des commandes sur la période (filtre fournisseur/pièce si sélectionnés)
            spend_total = self._compute_spend_total(session, start, end, supplier_id, piece_id)

            # Savings = somme((moyenne_offres - prix_selectionne) * qte) pour AO clos et transformés sur la période
            savings_total, savings_rows = self._compute_savings_option_a(session, start, end, supplier_id, piece_id)

            savings_rate = (Decimal("0") if spend_total == 0 else (savings_total / spend_total))

            # KPIs
            self.view.spend_total_label.setText(self.view.tr(f"Total spend: {spend_total}"))
            self.view.savings_total_label.setText(self.view.tr(f"Savings: {savings_total}"))
            self.view.savings_rate_label.setText(self.view.tr(f"Savings rate: {round(savings_rate * 100, 2)}%"))

            # Table Savings par AO
            self._populate_savings_table(savings_rows)

            # Tendance prix moyen par pièce (placeholder simple)
            self._populate_price_trend(session, start, end, supplier_id, piece_id)

        except Exception as e:
            print(f"ERROR load_data (financial): {e}")
            QMessageBox.warning(self.view, self.view.tr("Error"), str(e))
        finally:
            session.close()

    def _compute_spend_total(self, session, start, end, supplier_id, piece_id):
        total = Decimal("0")
        q = (
            session.query(LigneCommande, Commande)
            .join(Commande, LigneCommande.commande_id == Commande.id_commande)
            .filter(Commande.date_commande >= start, Commande.date_commande <= end)
        )
        if supplier_id:
            q = q.filter(Commande.fournisseur_id == supplier_id)
        if piece_id:
            q = q.filter(LigneCommande.piece_id == piece_id)

        for lc, cmd in q.all():
            qte = getattr(lc, 'quantite_commandee', 0) or 0
            pu = getattr(lc, 'prix_unitaire_ht', 0) or 0
            total += Decimal(str(pu)) * Decimal(str(qte))
        return total

    def _compute_savings_option_a(self, session, start, end, supplier_id, piece_id):
        """
        Compute savings by comparing each Envoyee order line price against
        the average of all offers received for the same piece across all AOs.
        """
        savings_total = Decimal("0")
        rows = []

        # Get Envoyee command lines in the date range
        q = (
            session.query(LigneCommande, Commande, Fournisseur)
            .join(Commande, LigneCommande.commande_id == Commande.id_commande)
            .join(Fournisseur, Commande.fournisseur_id == Fournisseur.id_fournisseur)
            .filter(
                Commande.statut == 'Envoyee',
                Commande.date_commande >= start,
                Commande.date_commande <= end
            )
        )
        if supplier_id:
            q = q.filter(Commande.fournisseur_id == supplier_id)
        if piece_id:
            q = q.filter(LigneCommande.piece_id == piece_id)

        for lc, cmd, fournisseur in q.all():
            qte = getattr(lc, 'quantite_commandee', 0) or 0
            prix_sel = Decimal(str(getattr(lc, 'prix_unitaire_ht', 0) or 0))
            pid = getattr(lc, 'piece_id', None)

            if not pid or qte == 0:
                continue

            # Get average offers price for this piece (across all AOs in period)
            avg_offre = self._average_offers_price_for_piece(session, None, pid, start, end)

            if avg_offre is None or avg_offre == Decimal("0"):
                continue

            saving = (avg_offre - prix_sel) * Decimal(str(qte))
            savings_total += saving

            rows.append({
                "ao_ref": cmd.numero_commande or str(cmd.id_commande),
                "piece_ref": str(pid),
                "fournisseur": fournisseur.nom,
                "qte": qte,
                "prix_sel": prix_sel,
                "prix_moy_offres": avg_offre,
                "savings": saving,
            })

        return savings_total, rows

    def _average_offers_price_for_piece(self, session, ao_id, piece_id, start=None, end=None):
        """
        Returns the average offers price for a given piece across all offers.
        If ao_id is provided, filters by specific AO.
        If start/end are provided, filters by the offer's AO creation date.
        """
        if piece_id is None:
            return None
        try:
            q = (
                session.query(func.avg(OffreRecueLigne.prix_unitaire_ht_propose))
                .join(OffreRecue, OffreRecueLigne.offre_id == OffreRecue.id_offre)
                .filter(OffreRecueLigne.piece_id == piece_id)
            )
            if ao_id is not None:
                q = q.filter(OffreRecue.ao_id == ao_id)
            if start is not None and end is not None:
                q = q.join(AppelOffre, OffreRecue.ao_id == AppelOffre.id_ao)
                q = q.filter(
                    AppelOffre.date_creation >= start,
                    AppelOffre.date_creation <= end
                )
            result = q.scalar()
            if result is not None:
                return Decimal(str(result))
            return None
        except Exception:
            return None

    def _populate_savings_table(self, rows):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels([
            self.view.tr("RFQ"), self.view.tr("Item"), self.view.tr("Supplier"),
            self.view.tr("Qty"), self.view.tr("Selected price"), self.view.tr("Average offers price"), self.view.tr("Savings")
        ])

        for r in rows:
            model.appendRow([
                QStandardItem(str(r.get("ao_ref", ""))),
                QStandardItem(str(r.get("piece_ref", ""))),
                QStandardItem(str(r.get("fournisseur", ""))),
                QStandardItem(str(r.get("qte", 0))),
                QStandardItem(str(r.get("prix_sel", 0))),
                QStandardItem(str(r.get("prix_moy_offres", 0))),
                QStandardItem(str(r.get("savings", 0))),
            ])

        self.view.savings_table.setModel(model)
        self.view.savings_table.resizeColumnsToContents()

    def _populate_price_trend(self, session, start, end, supplier_id, piece_id):
        """Placeholder: Prix moyen par pièce sur la période (table simple)."""
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels([self.view.tr("Reference"), self.view.tr("Designation"), self.view.tr("Average price")])

        # Calcul simple: moyenne des prix unitaires commandés par pièce
        sums = defaultdict(Decimal)
        counts = defaultdict(int)

        q = (
            session.query(LigneCommande, Article, Commande)
            .join(Article, LigneCommande.piece_id == Article.id_piece)
            .join(Commande, LigneCommande.commande_id == Commande.id_commande)
            .filter(Commande.date_commande >= start, Commande.date_commande <= end)
        )
        if supplier_id:
            q = q.filter(Commande.fournisseur_id == supplier_id)
        if piece_id:
            q = q.filter(LigneCommande.piece_id == piece_id)

        for lc, art, cmd in q.all():
            pu = Decimal(str(getattr(lc, 'prix_unitaire_ht', 0) or 0))
            key = (art.reference, art.designation)
            sums[key] += pu
            counts[key] += 1

        for (ref, des), _ in sorted(sums.items(), key=lambda x: x[1], reverse=True)[:100]:
            avg = sums[(ref, des)] / counts[(ref, des)] if counts[(ref, des)] else Decimal("0")
            model.appendRow([
                QStandardItem(str(ref)),
                QStandardItem(des or ""),
                QStandardItem(str(round(avg, 4)))
            ])

        self.view.price_trend_table.setModel(model)
        self.view.price_trend_table.resizeColumnsToContents()
