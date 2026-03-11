# routes/albums.py — dashboard e CRUD de álbuns
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from extensions import supabase

albums_bp = Blueprint("albums", __name__)


@albums_bp.route("/dashboard")
@login_required
def dashboard():
    """Página principal com todos os álbuns do usuário."""
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
    return render_template("dashboard.html", albums=albums, user=current_user)


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


@albums_bp.route("/albums/<album_id>")
@login_required
def album_detail(album_id):
    """Página de galeria de um álbum."""
    album_result = (
        supabase.table("albums")
        .select("*")
        .eq("id", album_id)
        .eq("user_id", current_user.id)  # garante que é do usuário
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
