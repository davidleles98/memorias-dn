# routes/photos.py
import cloudinary.uploader
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from extensions import supabase

photos_bp = Blueprint("photos", __name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@photos_bp.route("/albums/<album_id>/upload", methods=["POST"])
@login_required
def upload_photo(album_id):
    files = request.files.getlist("photos")
    if not files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    uploaded = []
    for file in files:
        if not file or not allowed_file(file.filename):
            continue

        result = cloudinary.uploader.upload(
            file,
            folder=f"memorias/{current_user.id}",
            transformation=[
                {"quality": "auto", "fetch_format": "auto"},
                {"width": 2000, "crop": "limit"},
            ],
        )
        url = result["secure_url"]
        public_id = result["public_id"]

        supabase.table("photos").insert({
            "album_id": album_id,
            "user_id": current_user.id,
            "url": url,
            "cloudinary_id": public_id,
            "caption": None,
        }).execute()

        photo_result = (
            supabase.table("photos")
            .select("*")
            .eq("album_id", album_id)
            .eq("cloudinary_id", public_id)
            .single()
            .execute()
        )
        photo = photo_result.data
        uploaded.append(photo)

    if uploaded:
        album = supabase.table("albums").select("cover_url").eq("id", album_id).single().execute().data
        if album and not album.get("cover_url"):
            supabase.table("albums").update({"cover_url": uploaded[0]["url"]}).eq("id", album_id).execute()

    return jsonify({"photos": uploaded})


@photos_bp.route("/photos/<photo_id>/caption", methods=["POST"])
@login_required
def update_caption(photo_id):
    """Atualiza a legenda de uma foto via AJAX."""
    data = request.get_json()
    caption = (data.get("caption") or "").strip() or None
    supabase.table("photos").update({"caption": caption}).eq("id", photo_id).eq("user_id", current_user.id).execute()
    return jsonify({"ok": True, "caption": caption})


@photos_bp.route("/photos/<photo_id>/delete", methods=["POST"])
@login_required
def delete_photo(photo_id):
    photo = (
        supabase.table("photos")
        .select("*")
        .eq("id", photo_id)
        .eq("user_id", current_user.id)
        .single()
        .execute()
        .data
    )
    if not photo:
        return jsonify({"error": "Foto não encontrada"}), 404
    try:
        cloudinary.uploader.destroy(photo["cloudinary_id"])
    except Exception:
        pass
    supabase.table("photos").delete().eq("id", photo_id).execute()
    return jsonify({"ok": True})
