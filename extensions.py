# extensions.py — instâncias compartilhadas entre módulos
import os
import cloudinary
from flask_login import LoginManager
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# ── Supabase ──────────────────────────────────────────────
supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)

# ── Cloudinary ────────────────────────────────────────────
cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
)

# ── Flask-Login ───────────────────────────────────────────
login_manager = LoginManager()
