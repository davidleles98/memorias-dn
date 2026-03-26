# models.py
from flask import session
from flask_login import UserMixin
from extensions import login_manager, supabase


class User(UserMixin):
    def __init__(self, id: str, email: str, name: str = "", approved: bool = False, is_admin: bool = False):
        self.id = id
        self.email = email
        self.name = name or email.split("@")[0]
        self.approved = approved
        self.is_admin = is_admin

    def get_id(self) -> str:
        return self.id


def _load_profile(user_id: str):
    """Busca o perfil do usuário na tabela profiles."""
    try:
        result = (
            supabase.table("profiles")
            .select("*")
            .eq("id", user_id)
            .single()
            .execute()
        )
        return result.data
    except Exception:
        return None


@login_manager.user_loader
def load_user(user_id: str):
    # Tenta via perfil
    profile = _load_profile(user_id)
    if profile:
        return User(
            id=user_id,
            email=profile.get("email", ""),
            name=profile.get("display_name", ""),
            approved=profile.get("approved", False),
            is_admin=profile.get("is_admin", False),
        )
    # Fallback pela sessão
    if session.get("user_id") == user_id:
        return User(
            id=user_id,
            email=session.get("user_email", ""),
            name=session.get("user_name", ""),
            approved=False,
        )
    return None