from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import event
from config import Config
import json

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message = 'Для доступа к этой странице необходимо авторизоваться.'


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    # Регистрируем фильтр для шаблонов
    @app.template_filter('from_json')
    def from_json_filter(value):
        if not value:
            return None
        try:
            return json.loads(value)
        except:
            return value

    with app.app_context():
        @event.listens_for(db.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    # Импорт моделей
    from app import models

    # Импорт и регистрация Blueprint
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Создание таблиц при первом запуске
    with app.app_context():
        db.create_all()

    return app