from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./chat.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
# ça sert à quoi le database.py? 
# C'est pour créer une connexion à la base de données et à définir une session pour interagir avec. Y'a aussi une classe de base pour les modèles de données qui seront utilisés dans l'appli.