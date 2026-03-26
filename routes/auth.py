# routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_user, logout_user, current_user
from extensions import supabase
from models import User, _load_profile

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        if not current_user.approved:
            return redirect(url_for("auth.pending"))
        return redirect(url_for("albums.dashboard"))
    return redirect(url_for("auth.login_page"))


@auth_bp.route("/login", methods=["GET"])
def login_page():
    if current_user.is_authenticated:
        if not current_user.approved:
            return redirect(url_for("auth.pending"))
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
            flash("E-mail ou senha incorretos.", "error")
            return redirect(url_for("auth.login_page"))

        profile = _load_profile(u.id)
        approved = profile.get("approved", False) if profile else False
        is_admin = profile.get("is_admin", False) if profile else False
        name = profile.get("display_name", "") if profile else ""

        user = User(id=u.id, email=u.email, name=name, approved=approved, is_admin=is_admin)
        login_user(user, remember=True)
        session["user_id"] = u.id
        session["user_email"] = u.email
        session["user_name"] = name
        session["access_token"] = resp.session.access_token

        if not approved:
            return redirect(url_for("auth.pending"))
        return redirect(url_for("albums.dashboard"))

    except Exception as e:
        err = str(e)
        if "Invalid login credentials" in err:
            flash("E-mail ou senha incorretos.", "error")
        elif "Email not confirmed" in err:
            flash("Confirme seu e-mail antes de entrar.", "error")
        else:
            flash(f"Erro: {err}", "error")
        return redirect(url_for("auth.login_page"))


@auth_bp.route("/signup", methods=["POST"])
def signup():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    name = request.form.get("name", "").strip()
    try:
        resp = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"full_name": name}},
        })
        if resp.session:
            u = resp.user
            profile = _load_profile(u.id)
            approved = profile.get("approved", False) if profile else False
            is_admin = profile.get("is_admin", False) if profile else False
            user = User(id=u.id, email=u.email, name=name, approved=approved, is_admin=is_admin)
            login_user(user, remember=True)
            session["user_id"] = u.id
            session["user_email"] = u.email
            session["user_name"] = name
            session["access_token"] = resp.session.access_token
            if not approved:
                return redirect(url_for("auth.pending"))
            return redirect(url_for("albums.dashboard"))

        flash("Conta criada! Verifique seu e-mail para confirmar.", "success")
        return redirect(url_for("auth.login_page"))
    except Exception as e:
        err = str(e)
        if "already registered" in err or "already exists" in err:
            flash("Este e-mail já está cadastrado.", "error")
        else:
            flash(f"Erro: {err}", "error")
        return redirect(url_for("auth.login_page"))


@auth_bp.route("/pending")
def pending():
    """Página de espera para usuários aguardando aprovação."""
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login_page"))
    if current_user.approved:
        return redirect(url_for("albums.dashboard"))
    return render_template("pending.html", user=current_user)


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    email = request.form.get("email", "").strip()
    try:
        supabase.auth.reset_password_email(email)
    except Exception:
        pass
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