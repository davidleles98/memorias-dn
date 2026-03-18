# routes/music.py — upload e listagem de músicas
import cloudinary.uploader
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from extensions import supabase

music_bp = Blueprint("music", __name__)

ALLOWED_AUDIO = {"mp3", "wav", "ogg", "m4a", "aac", "flac"}

def allowed_audio(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_AUDIO


@music_bp.route("/music", methods=["GET"])
@login_required
def list_music():
    result = (
        supabase.table("music")
        .select("*")
        .eq("user_id", current_user.id)
        .order("created_at", desc=False)
        .execute()
    )
    return jsonify({"tracks": result.data or []})


@music_bp.route("/music/upload", methods=["POST"])
@login_required
def upload_music():
    file = request.files.get("track")
    title = (request.form.get("title") or "").strip()

    if not file or not allowed_audio(file.filename):
        return jsonify({"error": "Arquivo inválido"}), 400

    if not title:
        # usa o nome do arquivo sem extensão
        title = file.filename.rsplit(".", 1)[0]

    # Cloudinary aceita áudio com resource_type="video"
    result = cloudinary.uploader.upload(
        file,
        resource_type="video",
        folder=f"memorias/{current_user.id}/music",
    )

    track = supabase.table("music").insert({
        "user_id": current_user.id,
        "title": title,
        "url": result["secure_url"],
        "cloudinary_id": result["public_id"],
        "duration": int(result.get("duration") or 0),
    }).select().execute().data

    # pega o primeiro resultado
    track_data = track[0] if track else {}
    return jsonify({"track": track_data})


@music_bp.route("/music/<track_id>/delete", methods=["POST"])
@login_required
def delete_music(track_id):
    track = (
        supabase.table("music")
        .select("*")
        .eq("id", track_id)
        .eq("user_id", current_user.id)
        .single()
        .execute()
        .data
    )
    if not track:
        return jsonify({"error": "Não encontrado"}), 404

    try:
        cloudinary.uploader.destroy(track["cloudinary_id"], resource_type="video")
    except Exception:
        pass

    supabase.table("music").delete().eq("id", track_id).execute()
    return jsonify({"ok": True})