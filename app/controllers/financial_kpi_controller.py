import logging
from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QMessageBox
from sqlalchemy import func
from decimal import Decimal
from collections import defaultdict

from database import get_db_session
from app.models.purchase_models import AppelOffre, Commande, LigneCommande, OffreRecue, OffreRecueLigne
from app.models.shared_models import Fournisseur, Article
from app.utils.kpi_helpers import line_total, PopulateFiltersMixin

log = logging.getLogger(__name__)


class FinancialKpiController(QObject, PopulateFiltersMixin):
    """Financial KPI controller.

    Calculates: total spend, savings (offers average vs selected price),
    savings rate, savings by RFQ table, and average price trend.
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
            # Total spend: sum of order amounts in period
            spend_total = self._compute_spend_total(session, start, end, supplier_id, piece_id)

            # Savings: (average_offers - selected_price) * qty for closed, converted RFQs
            savings_total, savings_rows = self._compute_savings_option_a(session, start, end, supplier_id, piece_id)

            savings_rate = Decimal("0") if spend_total == 0 else (savings_total / spend_total)

            # KPIs
            self.view.spend_total_label.setText(self.view.tr(f"Total spend: {spend_total}"))
            self.view.savings_total_label.setText(self.view.tr(f"Savings: {savings_total}"))
            self.view.savings_rate_label.setText(self.view.tr(f"Savings rate: {round(savings_rate * 100, 2)}%"))

            # Savings by RFQ table
            self._populate_savings_table(savings_rows)

            # Average price trend by item
            self._populate_price_trend(session, start, end, supplier_id, piece_id)

        except Exception:
            log.exception("Error loading financial KPI data:")
            QMessageBox.warning(self.view, self.view.tr("Error"), self.view.tr("Could not load financial data."))
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
            total += line_total(lc)
        return total

    def _compute_savings_option_a(self, session, start, end, supplier_id, piece_id):
        """Compute savings by comparing each Envoyee order line price against
        the average of all offers received for the same piece."""
        savings_total = Decimal("0")
        rows = []

        # Get Envoyee command lines in the date range
        q = (
            session.query(LigneCommande, Commande, Fournisseur)
            .join(Commande, LigneCommande.commande_id == Commande.id_commande)
            .join(Fournisseur, Commande.fournisseur_id == Fournisseur.id_fournisseur)
            .filter(
                Commande.statut == "Envoyee",
                Commande.date_commande >= start,
                Commande.date_commande <= end
            )
        )
        if supplier_id:
            q = q.filter(Commande.fournisseur_id == supplier_id)
        if piece_id:
            q = q.filter(LigneCommande.piece_id == piece_id)

        for lc, cmd, fournisseur in q.all():
            qte = getattr(lc, "quantite_commandee", 0) or 0
            prix_sel = Decimal(str(getattr(lc, "prix_unitaire_ht", 0) or 0))
            pid = getattr(lc, "piece_id", None)

            if not pid or qte == 0:
                continue

            # Average offers price for this piece (across all RFQs in period)
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
        """Returns the average offers price for a given piece across all offers.

        If ao_id is provided, filters by specific RFQ.
        If start/end are provided, filters by RFQ creation date.
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
            self.view.tr("Qty"), self.view.tr("Selected price"),
            self.view.tr("Average offers price"), self.view.tr("Savings")
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
        """Average price per item over period (simple table)."""
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels([
            self.view.tr("Reference"), self.view.tr("Designation"),
            self.view.tr("Average price")
        ])

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
            pu = Decimal(str(getattr(lc, "prix_unitaire_ht", 0) or 0))
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
