# models.py
from flask import session
from flask_login import UserMixin
from extensions import login_manager, supabase


class User(UserMixin):
    def __init__(self, id: str, email: str, name: str = ""):
        self.id = id
        self.email = email
        self.name = name or email.split("@")[0]

    def get_id(self) -> str:
        return self.id


@login_manager.user_loader
def load_user(user_id: str):
    # Tenta via API admin primeiro
    try:
        result = supabase.auth.admin.get_user_by_id(user_id)
        u = result.user
        if u:
            meta = u.user_metadata or {}
            return User(id=u.id, email=u.email, name=meta.get("full_name", ""))
    except Exception:
        pass

    # Fallback: reconstrói a partir da sessão Flask (salva no login)
    if session.get("user_id") == user_id:
        return User(
            id=user_id,
            email=session.get("user_email", ""),
            name=session.get("user_name", ""),
        )

    return None