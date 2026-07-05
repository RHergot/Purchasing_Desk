"""Shared utilities for KPI controllers — mixin and helpers."""

import logging
from decimal import Decimal

log = logging.getLogger(__name__)


def line_total(lc, default: Decimal = Decimal("0")) -> Decimal:
    """Compute total amount for a LigneCommande row safely.

    Returns price * quantity, handling None values gracefully.
    """
    qte = getattr(lc, "quantite_commandee", 0) or 0
    pu = getattr(lc, "prix_unitaire_ht", 0) or 0
    return Decimal(str(pu)) * Decimal(str(qte))


class PopulateFiltersMixin:
    """Mixin that populates supplier and piece filter combos.

    Expects self.view to have:
        - supplier_combo: QComboBox with currentData() and addItem()
        - piece_combo: QComboBox with currentData() and addItem()

    Requires get_db_session, Fournisseur, and Article in scope.
    """

    def populate_filters(self):
        from database import get_db_session
        from app.models.shared_models import Fournisseur, Article

        session = next(get_db_session())
        try:
            # Suppliers
            self.view.supplier_combo.blockSignals(True)
            self.view.supplier_combo.clear()
            self.view.supplier_combo.addItem(self.view.tr("All suppliers"), None)
            for f in session.query(Fournisseur).order_by(Fournisseur.nom.asc()).all():
                self.view.supplier_combo.addItem(f.nom, f.id_fournisseur)
            self.view.supplier_combo.blockSignals(False)

            # Pieces
            self.view.piece_combo.blockSignals(True)
            self.view.piece_combo.clear()
            self.view.piece_combo.addItem(self.view.tr("All items"), None)
            for a in session.query(Article).order_by(Article.reference.asc()).all():
                self.view.piece_combo.addItem(f"{a.reference} - {a.designation}", a.id_piece)
            self.view.piece_combo.blockSignals(False)
        except Exception:
            log.exception("Error populating filters:")
        finally:
            session.close()
