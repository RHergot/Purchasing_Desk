"""
Public API for the Purchasing Desk application.

Import controllers and utilities from here for simplified usage:
    from app import OrdersKpiController, FinancialKpiController
"""

from app.controllers.ao_detail_controller import AoDetailController
from app.controllers.ao_list_controller import AoListController
from app.controllers.financial_kpi_controller import FinancialKpiController
from app.controllers.negotiations_controller import NegotiationsController
from app.controllers.orders_kpi_controller import OrdersKpiController
from app.controllers.piece_list_controller import PieceListController
from app.controllers.pr_controller import PurchaseRequisitionController

from app.utils.pdf_generator import generate_purchase_order_pdf, generate_rfq_pdf
from app.utils.kpi_helpers import line_total, PopulateFiltersMixin

__all__ = [
    "AoDetailController",
    "AoListController",
    "FinancialKpiController",
    "NegotiationsController",
    "OrdersKpiController",
    "PieceListController",
    "PurchaseRequisitionController",
    "generate_purchase_order_pdf",
    "generate_rfq_pdf",
    "line_total",
    "PopulateFiltersMixin",
]
