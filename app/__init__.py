from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from config import Config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # ВАЖНО для SQLite: принудительно включаем поддержку внешних ключей (Foreign Keys)
    # По умолчанию в SQLite они отключены, что может привести к нарушению целостности.
    @event.listens_for(db.engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Импорт моделей здесь, чтобы избежать циклических зависимостей
    from app import models

    # Создание таблиц при первом запуске (для разработки удобно)
    with app.app_context():
        db.create_all()

    return app