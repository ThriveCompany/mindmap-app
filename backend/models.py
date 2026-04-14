from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    games_played = Column(Integer, default=0)

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    user_number = Column(Integer)
    system_number = Column(Integer)
    min_range = Column(Integer, default=1)
    max_range = Column(Integer, default=100)
    current_min = Column(Integer)
    current_max = Column(Integer)
    status = Column(String, default="active")  # active, won, lost
