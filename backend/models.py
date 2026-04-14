from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    games_played: Mapped[int] = mapped_column(Integer, default=0)
    total_guesses: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    average_guesses_per_game: Mapped[float] = mapped_column(Float, default=0.0)

    games: Mapped[List[Game]] = relationship("Game", back_populates="user")
    achievements: Mapped[List[UserAchievement]] = relationship("UserAchievement", back_populates="user")
    tournament_entries: Mapped[List[TournamentEntry]] = relationship("TournamentEntry", back_populates="user")

class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    tournament_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tournaments.id"), nullable=True, index=True)
    user_number: Mapped[int] = mapped_column(Integer)
    system_number: Mapped[int] = mapped_column(Integer)
    min_range: Mapped[int] = mapped_column(Integer, default=1)
    max_range: Mapped[int] = mapped_column(Integer, default=100)
    current_min: Mapped[int] = mapped_column(Integer)
    current_max: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, default="active")
    total_guesses: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    game_mode: Mapped[str] = mapped_column(String, default="classic")

    user: Mapped[User] = relationship("User", back_populates="games")
    tournament: Mapped[Optional[Tournament]] = relationship("Tournament", back_populates="games")
    moves: Mapped[List[GameMove]] = relationship("GameMove", back_populates="game", order_by="GameMove.created_at")

class GameMove(Base):
    __tablename__ = "game_moves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.id"), index=True)
    guess: Mapped[int] = mapped_column(Integer)
    result: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    game: Mapped[Game] = relationship("Game", back_populates="moves")

class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    creator_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="open")
    max_players: Mapped[int] = mapped_column(Integer, default=8)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    winner_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    entries: Mapped[List[TournamentEntry]] = relationship("TournamentEntry", back_populates="tournament")
    games: Mapped[List[Game]] = relationship("Game", back_populates="tournament")

class TournamentEntry(Base):
    __tablename__ = "tournament_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tournament_id: Mapped[int] = mapped_column(Integer, ForeignKey("tournaments.id"), index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String, default="active")
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    points: Mapped[int] = mapped_column(Integer, default=0)

    tournament: Mapped[Tournament] = relationship("Tournament", back_populates="entries")
    user: Mapped[User] = relationship("User", back_populates="tournament_entries")

    __table_args__ = (UniqueConstraint("tournament_id", "user_id", name="unique_tournament_user"),)

class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str] = mapped_column(Text)
    icon_url: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    requirement_type: Mapped[str] = mapped_column(String)
    requirement_value: Mapped[int] = mapped_column(Integer)
    points: Mapped[int] = mapped_column(Integer, default=0)
    rarity: Mapped[str] = mapped_column(String, default="common")

    user_achievements: Mapped[List[UserAchievement]] = relationship("UserAchievement", back_populates="achievement")

class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    achievement_id: Mapped[int] = mapped_column(Integer, ForeignKey("achievements.id"), index=True)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship("User", back_populates="achievements")
    achievement: Mapped[Achievement] = relationship("Achievement", back_populates="user_achievements")

    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="unique_user_achievement"),)
