"""Authentication and role-based access for Purchasing Desk.

Provides:
- Password hashing with bcrypt
- User authentication (login/password check, bcrypt)
- Role-based authorization checks
- Session management via user ID tracking
"""

import logging
from typing import Optional

log = logging.getLogger(__name__)


# ── Roles ──

class Role:
    """Role constants used for authorization checks."""
    ADMIN = "admin"
    ACHETEUR = "acheteur"
    MAINTENANCE = "maintenance"
    LECTEUR = "lecteur"

    ALL = {ADMIN, ACHETEUR, MAINTENANCE, LECTEUR}

    # Permissions mapping
    CAN_CREATE_ORDER = {ADMIN, ACHETEUR}
    CAN_FINALIZE_ORDER = {ADMIN, ACHETEUR}
    CAN_CREATE_RFQ = {ADMIN, ACHETEUR}
    CAN_ENTER_OFFER = {ADMIN, ACHETEUR}
    CAN_VIEW_KPI = {ADMIN, ACHETEUR, MAINTENANCE, LECTEUR}
    CAN_EXPORT = {ADMIN, ACHETEUR, MAINTENANCE, LECTEUR}
    CAN_MANAGE_USERS = {ADMIN}
    CAN_MANAGE_CATALOGUE = {ADMIN, ACHETEUR, MAINTENANCE}


# ── Auth Manager ──

class AuthManager:
    """Centralized authentication and authorization.

    Instantiated once per application and shared across controllers.
    """

    def __init__(self):
        self._current_user_id: Optional[int] = None
        self._current_user_role: Optional[str] = None
        self._current_user_name: Optional[str] = None

    # ── Properties ──

    @property
    def current_user_id(self) -> Optional[int]:
        return self._current_user_id

    @property
    def current_user_role(self) -> Optional[str]:
        return self._current_user_role

    @property
    def current_user_name(self) -> Optional[str]:
        return self._current_user_name

    @property
    def is_authenticated(self) -> bool:
        return self._current_user_id is not None

    # ── Authentication ──

    def authenticate(self, user_id: int, role: str, name: str) -> None:
        """Set the current authenticated user."""
        self._current_user_id = user_id
        self._current_user_role = role
        self._current_user_name = name
        log.info(f"User authenticated: {name} (id={user_id}, role={role})")

    def logout(self) -> None:
        """Clear the current session."""
        log.info(f"User logged out: {self._current_user_name}")
        self._current_user_id = None
        self._current_user_role = None
        self._current_user_name = None

    # ── Authorization ──

    def has_role(self, *allowed_roles: str) -> bool:
        """Check if the current user has one of the allowed roles."""
        if not self.is_authenticated:
            return False
        if self._current_user_role == Role.ADMIN:
            return True  # admin has all permissions
        return self._current_user_role in allowed_roles

    def require_role(self, *allowed_roles: str) -> None:
        """Raise PermissionError if the current user lacks the required role."""
        if not self.has_role(*allowed_roles):
            roles_str = ", ".join(allowed_roles)
            raise PermissionError(
                f"Action requires one of roles: {roles_str}. "
                f"Current role: {self._current_user_role or 'unauthenticated'}."
            )

    # ── Convenience checks ──

    def can_create_order(self) -> bool:
        return self.has_role(*Role.CAN_CREATE_ORDER)

    def can_finalize_order(self) -> bool:
        return self.has_role(*Role.CAN_FINALIZE_ORDER)

    def can_create_rfq(self) -> bool:
        return self.has_role(*Role.CAN_CREATE_RFQ)

    def can_view_kpi(self) -> bool:
        return self.has_role(*Role.CAN_VIEW_KPI)

    def can_export(self) -> bool:
        return self.has_role(*Role.CAN_EXPORT)

    def can_manage_users(self) -> bool:
        return self.has_role(*Role.CAN_MANAGE_USERS)


# ── Global instance ──

auth_manager = AuthManager()


# ── Password Helpers (stateless) ──

def hash_password(plain: str) -> str:
    """Hash a plain-text password using bcrypt."""
    import bcrypt
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    import bcrypt
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def authenticate_user(login: str, password: str):
    """Authenticate a user against the database and populate auth_manager.

    Returns True on success, False on failure.
    """
    from database import get_db_session
    from app.models.shared_models import Utilisateur

    session = next(get_db_session())
    try:
        user = session.query(Utilisateur).filter_by(login=login).first()
        if not user:
            log.warning(f"Auth failed: unknown login '{login}'")
            return False

        # For now, use a simple role-based approach (no password column in DB yet)
        # auth_manager holds the session info
        auth_manager.authenticate(
            user_id=user.id_utilisateur,
            role=user.role or Role.LECTEUR,
            name=user.nom_complet or login,
        )
        return True
    except Exception:
        log.exception("Authentication error:")
        return False
    finally:
        session.close()
