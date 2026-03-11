# routes/photos.py — upload de fotos para Cloudinary + salvar no Supabase
import cloudinary.uploader
from flask import Blueprint, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from extensions import supabase

photos_bp = Blueprint("photos", __name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@photos_bp.route("/albums/<album_id>/upload", methods=["POST"])
@login_required
def upload_photo(album_id):
    """
    Recebe uma ou mais fotos, faz upload para o Cloudinary
    e salva os metadados no Supabase.
    """
    files = request.files.getlist("photos")
    caption = request.form.get("caption", "").strip() or None

    if not files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    uploaded = []
    for file in files:
        if not file or not allowed_file(file.filename):
            continue

        # 1. Envia para o Cloudinary com otimização automática
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

        # 2. Salva metadados no Supabase
        photo = supabase.table("photos").insert({
            "album_id": album_id,
            "user_id": current_user.id,
            "url": url,
            "cloudinary_id": public_id,
            "caption": caption,
        }).select().single().execute().data

        uploaded.append(photo)

    # 3. Atualiza capa do álbum se ainda não tiver
    album = supabase.table("albums").select("cover_url").eq("id", album_id).single().execute().data
    if album and not album.get("cover_url") and uploaded:
        supabase.table("albums").update({"cover_url": uploaded[0]["url"]}).eq("id", album_id).execute()

    # Retorna JSON (o frontend faz o upload via fetch/AJAX)
    return jsonify({"photos": uploaded})


@photos_bp.route("/photos/<photo_id>/delete", methods=["POST"])
@login_required
def delete_photo(photo_id):
    """Deleta foto do Supabase (e opcionalmente do Cloudinary)."""
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

    # Remove do Cloudinary
    try:
        cloudinary.uploader.destroy(photo["cloudinary_id"])
    except Exception:
        pass  # continua mesmo se falhar no Cloudinary

    # Remove do Supabase
    supabase.table("photos").delete().eq("id", photo_id).execute()

    return jsonify({"ok": True})
