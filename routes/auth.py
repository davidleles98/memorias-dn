# routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_user, logout_user, current_user
from extensions import supabase
from models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
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
        if not u:
            flash("Não foi possível fazer login. Verifique seus dados.", "error")
            return redirect(url_for("auth.login_page"))
        meta = u.user_metadata or {}
        user = User(id=u.id, email=u.email, name=meta.get("full_name", ""))
        login_user(user, remember=True)
        session["user_id"] = u.id
        session["user_email"] = u.email
        session["user_name"] = meta.get("full_name", "")
        session["access_token"] = resp.session.access_token
        return redirect(url_for("albums.dashboard"))
    except Exception as e:
        err = str(e)
        if "Invalid login credentials" in err:
            flash("E-mail ou senha incorretos.", "error")
        elif "Email not confirmed" in err:
            flash("Confirme seu e-mail antes de entrar.", "error")
        else:
            flash(f"Erro ao entrar: {err}", "error")
        return redirect(url_for("auth.login_page"))


@auth_bp.route("/signup", methods=["POST"])
def signup():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    try:
        resp = supabase.auth.sign_up({"email": email, "password": password})
        if resp.session:
            u = resp.user
            meta = u.user_metadata or {}
            user = User(id=u.id, email=u.email, name=meta.get("full_name", ""))
            login_user(user, remember=True)
            session["user_id"] = u.id
            session["user_email"] = u.email
            session["access_token"] = resp.session.access_token
            return redirect(url_for("albums.dashboard"))
        flash("Conta criada! Verifique seu e-mail para confirmar.", "success")
        return redirect(url_for("auth.login_page"))
    except Exception as e:
        err = str(e)
        if "already registered" in err or "already exists" in err:
            flash("Este e-mail já está cadastrado. Tente entrar.", "error")
        else:
            flash(f"Erro ao criar conta: {err}", "error")
        return redirect(url_for("auth.login_page"))


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    email = request.form.get("email", "").strip()
    if not email:
        flash("Informe seu e-mail.", "error")
        return redirect(url_for("auth.login_page"))
    try:
        supabase.auth.reset_password_email(email)
        flash("E-mail de redefinição enviado! Verifique sua caixa de entrada.", "success")
    except Exception as e:
        # Retorna sucesso mesmo se o e-mail não existir (segurança)
        flash("Se este e-mail estiver cadastrado, você receberá as instruções.", "success")
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
