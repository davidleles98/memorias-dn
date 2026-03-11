# models.py — modelo de usuário para o Flask-Login
from flask_login import UserMixin
from extensions import login_manager, supabase


class User(UserMixin):
    """Representa o usuário logado na sessão."""

    def __init__(self, id: str, email: str, name: str = ""):
        self.id = id
        self.email = email
        self.name = name or email.split("@")[0]

    def get_id(self) -> str:
        return self.id


@login_manager.user_loader
def load_user(user_id: str):
    """Flask-Login chama isso para recarregar o usuário a cada request."""
    try:
        # Busca o usuário pelo ID na sessão do Supabase
        response = supabase.auth.admin.get_user_by_id(user_id)
        u = response.user
        if not u:
            return None
        meta = u.user_metadata or {}
        return User(id=u.id, email=u.email, name=meta.get("full_name", ""))
    except Exception:
        return None
