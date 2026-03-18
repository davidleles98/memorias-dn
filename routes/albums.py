# routes/albums.py
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from extensions import supabase

albums_bp = Blueprint("albums", __name__)


def _get_love_note(user_id: str) -> str:
    """Busca o texto da página inicial do usuário."""
    try:
        result = (
            supabase.table("settings")
            .select("love_note")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        return result.data.get("love_note") or ""
    except Exception:
        return ""


@albums_bp.route("/dashboard")
@login_required
def dashboard():
    result = (
        supabase.table("albums")
        .select("*, photos(count)")
        .eq("user_id", current_user.id)
        .order("created_at", desc=True)
        .execute()
    )
    albums = []
    for a in (result.data or []):
        albums.append({
            **a,
            "photo_count": a.get("photos", [{}])[0].get("count", 0) if a.get("photos") else 0,
        })
    love_note = _get_love_note(current_user.id)
    return render_template("dashboard.html", albums=albums, user=current_user, love_note=love_note)


@albums_bp.route("/settings/love-note", methods=["POST"])
@login_required
def save_love_note():
    """Salva (ou atualiza) o texto da página inicial."""
    data = request.get_json()
    text = (data.get("text") or "").strip()

    # Upsert: insere se não existir, atualiza se existir
    supabase.table("settings").upsert({
        "user_id": current_user.id,
        "love_note": text or None,
        "updated_at": "now()",
    }, on_conflict="user_id").execute()

    return jsonify({"ok": True})


@albums_bp.route("/albums/create", methods=["POST"])
@login_required
def create_album():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    if not name:
        return redirect(url_for("albums.dashboard"))
    supabase.table("albums").insert({
        "user_id": current_user.id,
        "name": name,
        "description": description or None,
    }).execute()
    return redirect(url_for("albums.dashboard"))


@albums_bp.route("/albums/<album_id>/edit", methods=["POST"])
@login_required
def edit_album(album_id):
    data = request.get_json()
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    if not name:
        return jsonify({"error": "Nome obrigatório"}), 400
    supabase.table("albums").update({
        "name": name,
        "description": description or None,
    }).eq("id", album_id).eq("user_id", current_user.id).execute()
    return jsonify({"ok": True, "name": name, "description": description})


@albums_bp.route("/albums/<album_id>/set-cover", methods=["POST"])
@login_required
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
        .eq("user_id", current_user.id)
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
def album_detail(album_id):
    album_result = (
        supabase.table("albums")
        .select("*")
        .eq("id", album_id)
        .eq("user_id", current_user.id)
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
def delete_album(album_id):
    supabase.table("albums").delete().eq("id", album_id).eq("user_id", current_user.id).execute()
    return redirect(url_for("albums.dashboard"))