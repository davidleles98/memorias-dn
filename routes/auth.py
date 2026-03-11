# routes/auth.py — login, cadastro, logout
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_user, logout_user, current_user
from extensions import supabase
from models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    """Redireciona para dashboard se logado, senão para login."""
    if current_user.is_authenticated:
        return redirect(url_for("albums.dashboard"))
    return redirect(url_for("auth.login_page"))


@auth_bp.route("/login", methods=["GET"])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("albums.dashboard"))
    return render_template("auth.html")


@auth_bp.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    try:
        resp = supabase.auth.sign_in_with_password({"email": email, "password": password})
        u = resp.user
        user = User(id=u.id, email=u.email, name=(u.user_metadata or {}).get("full_name", ""))
        login_user(user, remember=True)
        # Guarda o token Supabase na sessão para chamadas autenticadas
        session["access_token"] = resp.session.access_token
        return redirect(url_for("albums.dashboard"))
    except Exception as e:
        flash(f"Email ou senha incorretos.", "error")
        return redirect(url_for("auth.login_page"))


@auth_bp.route("/signup", methods=["POST"])
def signup():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    try:
        resp = supabase.auth.sign_up({"email": email, "password": password})
        flash("Conta criada! Verifique seu e-mail para confirmar.", "success")
        return redirect(url_for("auth.login_page"))
    except Exception as e:
        flash(f"Erro ao criar conta: {str(e)}", "error")
        return redirect(url_for("auth.login_page"))


@auth_bp.route("/logout")
def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    logout_user()
    session.clear()
    return redirect(url_for("auth.login_page"))
