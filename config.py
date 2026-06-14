import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Используем SQLite для разработки. Файл БД будет создан в корне проекта.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'university.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Секретный ключ для сессий (понадобится позже для авторизации)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'pskovsu-secret-key-2026'