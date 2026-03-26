# routes/albums.py
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from functools import wraps
from extensions import supabase

albums_bp = Blueprint("albums", __name__)


def approved_required(f):
    """Decorator: redireciona para /pending se não aprovado."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.approved:
            return redirect(url_for("auth.pending"))
        return f(*args, **kwargs)
    return decorated


def _get_settings() -> dict:
    """Settings são compartilhadas — pega a primeira linha existente."""
    try:
        result = supabase.table("settings").select("love_note, playlist_url").limit(1).execute()
        return result.data[0] if result.data else {}
    except Exception:
        return {}


def _get_all_approved_users():
    """Lista todos os usuários aprovados (para gerenciar membros)."""
    try:
        result = (
            supabase.table("profiles")
            .select("id, display_name, email")
            .eq("approved", True)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


@albums_bp.route("/dashboard")
@login_required
@approved_required
def dashboard():
    # Busca todos os álbuns visíveis para este usuário
    # (público OU limitado onde ele é membro)
    result = (
        supabase.table("albums")
        .select("*, photos(count)")
        .order("created_at", desc=True)
        .execute()
    )
    albums = []
    for a in (result.data or []):
        albums.append({
            **a,
            "photo_count": a.get("photos", [{}])[0].get("count", 0) if a.get("photos") else 0,
        })
    settings = _get_settings()
    return render_template(
        "dashboard.html",
        albums=albums,
        user=current_user,
        love_note=settings.get("love_note", ""),
        playlist_url=settings.get("playlist_url", ""),
    )


@albums_bp.route("/albums/create", methods=["POST"])
@login_required
@approved_required
def create_album():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    visibility = request.form.get("visibility", "public")
    if visibility not in ("public", "limited"):
        visibility = "public"
    if not name:
        return redirect(url_for("albums.dashboard"))
    supabase.table("albums").insert({
        "created_by": current_user.id,
        "name": name,
        "description": description or None,
        "visibility": visibility,
    }).execute()
    return redirect(url_for("albums.dashboard"))


@albums_bp.route("/albums/<album_id>/edit", methods=["POST"])
@login_required
@approved_required
def edit_album(album_id):
    data = request.get_json()
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    visibility = data.get("visibility", "public")
    if visibility not in ("public", "limited"):
        visibility = "public"
    if not name:
        return jsonify({"error": "Nome obrigatório"}), 400
    supabase.table("albums").update({
        "name": name,
        "description": description or None,
        "visibility": visibility,
    }).eq("id", album_id).execute()
    return jsonify({"ok": True, "name": name, "description": description, "visibility": visibility})


@albums_bp.route("/albums/<album_id>/members", methods=["GET"])
@login_required
@approved_required
def get_members(album_id):
    """Retorna membros do álbum + todos os usuários aprovados."""
    members = (
        supabase.table("album_members")
        .select("user_id")
        .eq("album_id", album_id)
        .execute()
        .data or []
    )
    member_ids = {m["user_id"] for m in members}
    all_users = _get_all_approved_users()
    return jsonify({
        "all_users": all_users,
        "member_ids": list(member_ids),
    })


@albums_bp.route("/albums/<album_id>/members", methods=["POST"])
@login_required
@approved_required
def set_members(album_id):
    """Substitui a lista de membros do álbum."""
    data = request.get_json()
    user_ids = data.get("user_ids", [])
    # Remove todos os membros antigos
    supabase.table("album_members").delete().eq("album_id", album_id).execute()
    # Insere os novos
    if user_ids:
        supabase.table("album_members").insert([
            {"album_id": album_id, "user_id": uid} for uid in user_ids
        ]).execute()
    return jsonify({"ok": True})


@albums_bp.route("/albums/<album_id>/set-cover", methods=["POST"])
@login_required
@approved_required
def set_cover(album_id):
    data = request.get_json()
    photo_url = (data.get("url") or "").strip()
    if not photo_url:
        return jsonify({"error": "URL obrigatória"}), 400
    photo = (
        supabase.table("photos")
        .select("id, url")
        .eq("url", photo_url)
        .eq("album_id", album_id)
        .single()
        .execute()
        .data
    )
    if not photo:
        return jsonify({"error": "Foto não encontrada"}), 404
    supabase.table("albums").update({"cover_url": photo["url"]}).eq("id", album_id).execute()
    return jsonify({"ok": True, "cover_url": photo["url"]})


@albums_bp.route("/albums/<album_id>")
@login_required
@approved_required
def album_detail(album_id):
    album_result = (
        supabase.table("albums")
        .select("*")
        .eq("id", album_id)
        .single()
        .execute()
    )
    if not album_result.data:
        return redirect(url_for("albums.dashboard"))
    photos_result = (
        supabase.table("photos")
        .select("*")
        .eq("album_id", album_id)
        .order("created_at")
        .execute()
    )
    return render_template(
        "gallery.html",
        album=album_result.data,
        photos=photos_result.data or [],
        user=current_user,
    )


@albums_bp.route("/albums/<album_id>/delete", methods=["POST"])
@login_required
@approved_required
def delete_album(album_id):
    supabase.table("albums").delete().eq("id", album_id).execute()
    return redirect(url_for("albums.dashboard"))


@albums_bp.route("/settings/love-note", methods=["POST"])
@login_required
@approved_required
def save_love_note():
    data = request.get_json()
    text = (data.get("text") or "").strip()
    # Upsert compartilhado — usa um ID fixo ou o do primeiro usuário
    _upsert_settings({"love_note": text or None})
    return jsonify({"ok": True})


@albums_bp.route("/settings/playlist", methods=["POST"])
@login_required
@approved_required
def save_playlist():
    data = request.get_json()
    url = (data.get("url") or "").strip()
    _upsert_settings({"playlist_url": url or None})
    return jsonify({"ok": True})


def _upsert_settings(fields: dict):
    """Settings compartilhadas: atualiza a linha existente ou cria uma."""
    existing = supabase.table("settings").select("id").limit(1).execute()
    if existing.data:
        row_id = existing.data[0]["id"]
        supabase.table("settings").update({**fields, "updated_at": "now()"}).eq("id", row_id).execute()
    else:
        supabase.table("settings").insert({**fields, "user_id": current_user.id}).execute()


# ── Painel admin ───────────────────────────────────────────

@albums_bp.route("/admin")
@login_required
def admin_panel():
    if not current_user.is_admin:
        return redirect(url_for("albums.dashboard"))
    pending = (
        supabase.table("profiles")
        .select("*")
        .eq("approved", False)
        .order("created_at")
        .execute()
        .data or []
    )
    approved = (
        supabase.table("profiles")
        .select("*")
        .eq("approved", True)
        .order("display_name")
        .execute()
        .data or []
    )
    return render_template("admin.html", pending=pending, approved=approved, user=current_user)


@albums_bp.route("/admin/approve/<user_id>", methods=["POST"])
@login_required
def approve_user(user_id):
    if not current_user.is_admin:
        return jsonify({"error": "Sem permissão"}), 403
    supabase.table("profiles").update({"approved": True}).eq("id", user_id).execute()
    return jsonify({"ok": True})


@albums_bp.route("/admin/revoke/<user_id>", methods=["POST"])
@login_required
def revoke_user(user_id):
    if not current_user.is_admin:
        return jsonify({"error": "Sem permissão"}), 403
    supabase.table("profiles").update({"approved": False}).eq("id", user_id).execute()
    return jsonify({"ok": True})