import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-motocicletas-123'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///motocicletas.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
