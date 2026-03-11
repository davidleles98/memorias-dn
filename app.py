# app.py — ponto de entrada da aplicação
import os
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager

from extensions import login_manager
from routes.auth import auth_bp
from routes.albums import albums_bp
from routes.photos import photos_bp

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ["SECRET_KEY"]

    # Inicializa o Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login_page"

    # Registra os blueprints (grupos de rotas)
    app.register_blueprint(auth_bp)
    app.register_blueprint(albums_bp)
    app.register_blueprint(photos_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
