from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import Base, User, Game, GameMove, Achievement, UserAchievement, Tournament, TournamentEntry
from .auth import get_password_hash, authenticate_user, create_access_token, verify_token

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            initialize_achievements(db)
        finally:
            db.close()
        print("Database tables created and achievements initialized successfully")
    except Exception as e:
        print(f"Database setup error: {e}")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    wins: int
    losses: int
    games_played: int
    win_rate: float
    best_streak: int
    current_streak: int
    total_guesses: int
    average_guesses_per_game: float
    created_at: datetime
    last_active: datetime

    class Config:
        orm_mode = True

class GameHistoryResponse(BaseModel):
    id: int
    user_number: int
    system_number: int
    status: str
    total_guesses: int
    game_mode: str
    created_at: datetime
    completed_at: Optional[datetime]
    moves: List[dict] = []

    class Config:
        orm_mode = True

class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    avatar_url: Optional[str]
    wins: int
    games_played: int
    win_rate: float
    best_streak: int

    class Config:
        orm_mode = True

class AchievementResponse(BaseModel):
    id: int
    name: str
    description: str
    icon_url: str
    category: str
    rarity: str
    points: int
    unlocked_at: Optional[datetime]

    class Config:
        orm_mode = True

class UserProfileUpdate(BaseModel):
    email: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class GameCreate(BaseModel):
    min_range: int = 1
    max_range: int = 100
    user_number: int
    tournament_id: Optional[int] = None

class Guess(BaseModel):
    guess: int

class GameResponse(BaseModel):
    id: int
    min_range: int
    max_range: int
    current_min: int
    current_max: int
    status: str
    messages: list[str] = []

    class Config:
        orm_mode = True

class TournamentEntryResponse(BaseModel):
    user_id: int
    username: str
    avatar_url: Optional[str]
    wins: int
    losses: int
    points: int
    joined_at: datetime
    status: str

    class Config:
        orm_mode = True

class TournamentSummaryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    max_players: int
    current_players: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True

class TournamentDetailResponse(TournamentSummaryResponse):
    winner_id: Optional[int]
    entries: List[TournamentEntryResponse] = []

    class Config:
        orm_mode = True

class TournamentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    max_players: int = 8

    class Config:
        orm_mode = True

class TournamentJoinResponse(BaseModel):
    tournament_id: int
    user_id: int
    status: str

    class Config:
        orm_mode = True

# Security
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    username = verify_token(token)
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def check_achievements(user: User, db: Session):
    """Check and unlock achievements for a user"""
    # Get all achievements
    achievements = db.query(Achievement).all()
    unlocked_ids = {ua.achievement_id for ua in user.achievements}

    for achievement in achievements:
        if achievement.id in unlocked_ids:
            continue  # Already unlocked

        unlocked = False

        # Check achievement requirements
        if achievement.requirement_type == "wins" and user.wins >= achievement.requirement_value:
            unlocked = True
        elif achievement.requirement_type == "games_played" and user.games_played >= achievement.requirement_value:
            unlocked = True
        elif achievement.requirement_type == "streak" and user.best_streak >= achievement.requirement_value:
            unlocked = True
        elif achievement.requirement_type == "first_win" and user.wins >= 1:
            unlocked = True
        elif achievement.requirement_type == "perfect_game" and user.average_guesses_per_game <= 7:  # Average of 7 or less guesses
            unlocked = True

        if unlocked:
            user_achievement = UserAchievement(user_id=user.id, achievement_id=achievement.id)
            db.add(user_achievement)

def initialize_achievements(db: Session):
    """Initialize default achievements if they don't exist"""
    achievements_data = [
        {"name": "First Victory", "description": "Win your first game", "icon_url": "🏆", "category": "gameplay", "requirement_type": "first_win", "requirement_value": 1, "points": 10, "rarity": "common"},
        {"name": "Winning Streak", "description": "Win 5 games in a row", "icon_url": "🔥", "category": "gameplay", "requirement_type": "streak", "requirement_value": 5, "points": 25, "rarity": "rare"},
        {"name": "Century Club", "description": "Play 100 games", "icon_url": "💯", "category": "gameplay", "requirement_type": "games_played", "requirement_value": 100, "points": 50, "rarity": "epic"},
        {"name": "Champion", "description": "Win 50 games", "icon_url": "👑", "category": "gameplay", "requirement_type": "wins", "requirement_value": 50, "points": 100, "rarity": "legendary"},
        {"name": "Perfectionist", "description": "Maintain an average of 7 or fewer guesses per game", "icon_url": "🎯", "category": "gameplay", "requirement_type": "perfect_game", "requirement_value": 7, "points": 75, "rarity": "epic"},
        {"name": "Dedicated Player", "description": "Play 10 games", "icon_url": "🎮", "category": "gameplay", "requirement_type": "games_played", "requirement_value": 10, "points": 15, "rarity": "common"},
    ]

    for data in achievements_data:
        existing = db.query(Achievement).filter(Achievement.name == data["name"]).first()
        if not existing:
            achievement = Achievement(**data)
            db.add(achievement)

    db.commit()

@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    # Hash password
    hashed_password = get_password_hash(user.password)
    # Create user
    db_user = User(username=user.username, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.username, user.password)
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserResponse)  # type: ignore
def read_users_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    wins = current_user.wins
    losses = current_user.losses
    games_played = current_user.games_played
    win_rate = (wins / games_played * 100) if games_played > 0 else 0.0
    avg_guesses = (current_user.total_guesses / games_played) if games_played > 0 else 0.0

    current_user.last_active = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "avatar_url": current_user.avatar_url,
        "bio": current_user.bio,
        "wins": wins,
        "losses": losses,
        "games_played": games_played,
        "win_rate": round(win_rate, 2),
        "best_streak": current_user.best_streak,
        "current_streak": current_user.current_streak,
        "total_guesses": current_user.total_guesses,
        "average_guesses_per_game": round(avg_guesses, 1),
        "created_at": current_user.created_at,
        "last_active": current_user.last_active
    }

@app.post("/games", response_model=GameResponse)
def create_game(game: GameCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not (game.min_range <= game.user_number <= game.max_range):
        raise HTTPException(status_code=400, detail="User number must be within range")

    tournament_id = None
    if game.tournament_id is not None:
        tournament = db.query(Tournament).filter(Tournament.id == game.tournament_id).first()
        if not tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")
        if tournament.status != "in_progress":
            raise HTTPException(status_code=400, detail="Tournament is not accepting new games")
        existing_entry = db.query(TournamentEntry).filter(
            TournamentEntry.tournament_id == tournament.id,
            TournamentEntry.user_id == current_user.id,
        ).first()
        if not existing_entry:
            raise HTTPException(status_code=403, detail="Must join tournament before playing")
        tournament_id = tournament.id

    import random
    system_number = random.randint(game.min_range, game.max_range)
    db_game = Game(
        user_id=current_user.id,
        tournament_id=tournament_id,
        user_number=game.user_number,
        system_number=system_number,
        min_range=game.min_range,
        max_range=game.max_range,
        current_min=game.min_range,
        current_max=game.max_range,
        game_mode="classic"
    )
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return {
        "id": db_game.id,
        "min_range": db_game.min_range,
        "max_range": db_game.max_range,
        "current_min": db_game.current_min,
        "current_max": db_game.current_max,
        "status": db_game.status,
        "messages": [f"Range: {db_game.min_range} – {db_game.max_range}", "Lock in your number", f"You locked: {db_game.user_number}"]
    }

@app.post("/games/{game_id}/guess", response_model=GameResponse)  # type: ignore
def submit_guess(game_id: int, guess_data: Guess, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id, Game.user_id == current_user.id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != "active":
        raise HTTPException(status_code=400, detail="Game is not active")
    if not (game.current_min <= guess_data.guess <= game.current_max):
        raise HTTPException(status_code=400, detail="Guess must be within current range")

    messages = [f"Is your number {guess_data.guess}?"]
    system_number = game.system_number

    if guess_data.guess < system_number:
        result = "low"
        messages.append("Higher ⬆️")
        game.current_min = guess_data.guess + 1
    elif guess_data.guess > system_number:
        result = "high"
        messages.append("Lower ⬇️")
        game.current_max = guess_data.guess - 1
    else:
        result = "correct"
        messages.append("Yes! You win 🎉")
        game.status = "won"
        game.completed_at = datetime.utcnow()
        current_user.wins += 1
        current_user.games_played += 1
        current_user.current_streak += 1
        if current_user.current_streak > current_user.best_streak:
            current_user.best_streak = current_user.current_streak

    game_move = GameMove(
        game_id=game.id,
        guess=guess_data.guess,
        result=result
    )
    db.add(game_move)

    game.total_guesses += 1
    current_user.total_guesses += 1

    if result == "correct":
        if game.tournament_id is not None:
            entry = db.query(TournamentEntry).filter(
                TournamentEntry.tournament_id == game.tournament_id,
                TournamentEntry.user_id == current_user.id,
            ).first()
            if entry:
                entry.wins += 1
                entry.points += max(0, 100 - game.total_guesses)

        check_achievements(current_user, db)
        current_user.average_guesses_per_game = current_user.total_guesses / current_user.games_played
        db.commit()
        return {
            "id": game.id,
            "min_range": game.min_range,
            "max_range": game.max_range,
            "current_min": game.current_min,
            "current_max": game.current_max,
            "status": game.status,
            "messages": messages
        }

    if game.current_min > game.current_max:
        messages.append("Impossible! You lose 😢")
        game.status = "lost"
        game.completed_at = datetime.utcnow()
        current_user.losses += 1
        current_user.games_played += 1
        current_user.current_streak = 0
        if game.tournament_id is not None:
            entry = db.query(TournamentEntry).filter(
                TournamentEntry.tournament_id == game.tournament_id,
                TournamentEntry.user_id == current_user.id,
            ).first()
            if entry:
                entry.losses += 1

        check_achievements(current_user, db)

    if current_user.games_played > 0:
        current_user.average_guesses_per_game = current_user.total_guesses / current_user.games_played

    db.commit()
    return {
        "id": game.id,
        "min_range": game.min_range,
        "max_range": game.max_range,
        "current_min": game.current_min,
        "current_max": game.current_max,
        "status": game.status,
        "messages": messages
    }

@app.get("/games/{game_id}", response_model=GameResponse)
def get_game(game_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id, Game.user_id == current_user.id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return {
        "id": game.id,
        "min_range": game.min_range,
        "max_range": game.max_range,
        "current_min": game.current_min,
        "current_max": game.current_max,
        "status": game.status,
        "messages": []
    }

# Phase 2 Endpoints

@app.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(limit: int = 50, db: Session = Depends(get_db)):
    """Get global leaderboard sorted by win rate, then wins"""
    users = db.query(User).filter(User.games_played >= 5).all()  # Minimum 5 games played

    leaderboard = []
    for user in users:
        win_rate = (user.wins / user.games_played * 100) if user.games_played > 0 else 0
        leaderboard.append({
            "user": user,
            "win_rate": win_rate
        })

    # Sort by win rate desc, then wins desc
    leaderboard.sort(key=lambda x: (x["win_rate"], x["user"].wins), reverse=True)

    result = []
    for i, entry in enumerate(leaderboard[:limit], 1):
        user = entry["user"]
        result.append({
            "rank": i,
            "username": user.username,
            "avatar_url": user.avatar_url,
            "wins": user.wins,
            "games_played": user.games_played,
            "win_rate": round(entry["win_rate"], 1),
            "best_streak": user.best_streak
        })

    return result

@app.get("/games/history", response_model=List[GameHistoryResponse])
def get_game_history(limit: int = 20, offset: int = 0, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's game history"""
    games = db.query(Game).filter(Game.user_id == current_user.id).order_by(desc(Game.created_at)).offset(offset).limit(limit).all()

    result = []
    for game in games:
        moves = []
        for move in game.moves:
            moves.append({
                "guess": move.guess,
                "result": move.result,
                "timestamp": move.created_at
            })

        result.append({
            "id": game.id,
            "user_number": game.user_number,
            "system_number": game.system_number,
            "status": game.status,
            "total_guesses": game.total_guesses,
            "game_mode": game.game_mode,
            "created_at": game.created_at,
            "completed_at": game.completed_at,
            "moves": moves
        })

    return result

@app.post("/tournaments", response_model=TournamentSummaryResponse)
def create_tournament(tournament_data: TournamentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tournament = Tournament(
        name=tournament_data.name,
        description=tournament_data.description,
        creator_id=current_user.id,
        max_players=tournament_data.max_players,
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    return {
        "id": tournament.id,
        "name": tournament.name,
        "description": tournament.description,
        "status": tournament.status,
        "max_players": tournament.max_players,
        "current_players": 0,
        "created_at": tournament.created_at,
        "started_at": tournament.started_at,
        "completed_at": tournament.completed_at,
    }

@app.get("/tournaments", response_model=List[TournamentSummaryResponse])
def list_tournaments(db: Session = Depends(get_db)):
    tournaments = db.query(Tournament).order_by(desc(Tournament.created_at)).all()
    result = []
    for tournament in tournaments:
        result.append({
            "id": tournament.id,
            "name": tournament.name,
            "description": tournament.description,
            "status": tournament.status,
            "max_players": tournament.max_players,
            "current_players": len(tournament.entries),
            "created_at": tournament.created_at,
            "started_at": tournament.started_at,
            "completed_at": tournament.completed_at,
        })
    return result

@app.get("/tournaments/{tournament_id}", response_model=TournamentDetailResponse)
def get_tournament(tournament_id: int, db: Session = Depends(get_db)):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    entries = []
    for entry in tournament.entries:
        user = db.query(User).filter(User.id == entry.user_id).first()
        entries.append({
            "user_id": entry.user_id,
            "username": user.username if user else "",
            "avatar_url": user.avatar_url if user else None,
            "wins": entry.wins,
            "losses": entry.losses,
            "points": entry.points,
            "joined_at": entry.joined_at,
            "status": entry.status,
        })

    return {
        "id": tournament.id,
        "name": tournament.name,
        "description": tournament.description,
        "status": tournament.status,
        "max_players": tournament.max_players,
        "current_players": len(tournament.entries),
        "created_at": tournament.created_at,
        "started_at": tournament.started_at,
        "completed_at": tournament.completed_at,
        "winner_id": tournament.winner_id,
        "entries": entries,
    }

@app.post("/tournaments/{tournament_id}/join", response_model=TournamentJoinResponse)
def join_tournament(tournament_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.status != "open":
        raise HTTPException(status_code=400, detail="Tournament is not open for joins")
    if len(tournament.entries) >= tournament.max_players:
        raise HTTPException(status_code=400, detail="Tournament is full")
    existing_entry = db.query(TournamentEntry).filter(
        TournamentEntry.tournament_id == tournament_id,
        TournamentEntry.user_id == current_user.id,
    ).first()
    if existing_entry:
        raise HTTPException(status_code=400, detail="Already joined")

    entry = TournamentEntry(
        tournament_id=tournament_id,
        user_id=current_user.id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {
        "tournament_id": tournament_id,
        "user_id": current_user.id,
        "status": entry.status,
    }

@app.post("/tournaments/{tournament_id}/start", response_model=TournamentDetailResponse)
def start_tournament(tournament_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can start the tournament")
    if tournament.status != "open":
        raise HTTPException(status_code=400, detail="Tournament cannot be started")
    if len(tournament.entries) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 players to start")

    tournament.status = "in_progress"
    tournament.started_at = datetime.utcnow()
    db.commit()
    db.refresh(tournament)

    entries = []
    for entry in tournament.entries:
        user = db.query(User).filter(User.id == entry.user_id).first()
        entries.append({
            "user_id": entry.user_id,
            "username": user.username if user else "",
            "avatar_url": user.avatar_url if user else None,
            "wins": entry.wins,
            "losses": entry.losses,
            "points": entry.points,
            "joined_at": entry.joined_at,
            "status": entry.status,
        })

    return {
        "id": tournament.id,
        "name": tournament.name,
        "description": tournament.description,
        "status": tournament.status,
        "max_players": tournament.max_players,
        "current_players": len(tournament.entries),
        "created_at": tournament.created_at,
        "started_at": tournament.started_at,
        "completed_at": tournament.completed_at,
        "winner_id": tournament.winner_id,
        "entries": entries,
    }

@app.get("/tournaments/{tournament_id}/standings", response_model=List[TournamentEntryResponse])
def get_tournament_standings(tournament_id: int, db: Session = Depends(get_db)):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    standings = []
    for entry in tournament.entries:
        user = db.query(User).filter(User.id == entry.user_id).first()
        standings.append({
            "user_id": entry.user_id,
            "username": user.username if user else "",
            "avatar_url": user.avatar_url if user else None,
            "wins": entry.wins,
            "losses": entry.losses,
            "points": entry.points,
            "joined_at": entry.joined_at,
            "status": entry.status,
        })

    standings.sort(key=lambda item: (item["points"], item["wins"]), reverse=True)
    return standings

@app.put("/profile", response_model=UserResponse)
def update_profile(profile_data: UserProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update user profile information"""
    if profile_data.email is not None:
        # Check if email is already taken
        existing_user = db.query(User).filter(User.email == profile_data.email, User.id != current_user.id).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = profile_data.email

    if profile_data.bio is not None:
        current_user.bio = profile_data.bio

    if profile_data.avatar_url is not None:
        current_user.avatar_url = profile_data.avatar_url

    db.commit()
    db.refresh(current_user)

    # Return updated user data
    wins = current_user.wins
    games_played = current_user.games_played
    win_rate = (wins / games_played * 100) if games_played > 0 else 0.0
    avg_guesses = (current_user.total_guesses / games_played) if games_played > 0 else 0.0

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "avatar_url": current_user.avatar_url,
        "bio": current_user.bio,
        "wins": wins,
        "losses": current_user.losses,
        "games_played": games_played,
        "win_rate": round(win_rate, 2),
        "best_streak": current_user.best_streak,
        "current_streak": current_user.current_streak,
        "total_guesses": current_user.total_guesses,
        "average_guesses_per_game": round(avg_guesses, 1),
        "created_at": current_user.created_at,
        "last_active": current_user.last_active
    }

@app.get("/achievements", response_model=List[AchievementResponse])
def get_user_achievements(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's unlocked achievements"""
    user_achievements = db.query(UserAchievement).filter(UserAchievement.user_id == current_user.id).all()

    result = []
    for ua in user_achievements:
        achievement = ua.achievement
        result.append({
            "id": achievement.id,
            "name": achievement.name,
            "description": achievement.description,
            "icon_url": achievement.icon_url,
            "category": achievement.category,
            "rarity": achievement.rarity,
            "points": achievement.points,
            "unlocked_at": ua.unlocked_at
        })

    return result

@app.get("/achievements/available")
def get_available_achievements(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all available achievements with unlock status"""
    all_achievements = db.query(Achievement).all()
    user_achievement_ids = {ua.achievement_id for ua in current_user.achievements}

    result = []
    for achievement in all_achievements:
        unlocked = achievement.id in user_achievement_ids
        unlock_time = None
        if unlocked:
            ua = next((ua for ua in current_user.achievements if ua.achievement_id == achievement.id), None)
            unlock_time = ua.unlocked_at if ua else None

        result.append({
            "id": achievement.id,
            "name": achievement.name,
            "description": achievement.description,
            "icon_url": achievement.icon_url,
            "category": achievement.category,
            "rarity": achievement.rarity,
            "points": achievement.points,
            "unlocked": unlocked,
            "unlocked_at": unlock_time
        })

    return result

@app.get("/stats/global")
def get_global_stats(db: Session = Depends(get_db)):
    """Get global statistics"""
    total_users = db.query(func.count(User.id)).scalar()
    total_games = db.query(func.count(Game.id)).scalar()
    completed_games = db.query(func.count(Game.id)).filter(Game.status.in_(["won", "lost"])).scalar()

    # Average guesses per game
    avg_guesses_result = db.query(func.avg(Game.total_guesses)).filter(Game.status.in_(["won", "lost"])).scalar()
    avg_guesses = float(avg_guesses_result) if avg_guesses_result else 0.0

    return {
        "total_users": total_users,
        "total_games": total_games,
        "completed_games": completed_games,
        "average_guesses_per_game": round(avg_guesses, 1),
        "active_games": total_games - completed_games
    }

@app.get("/version")
def version():
    return {"version": "2.0", "phase": "Phase 2 Complete", "features": ["leaderboards", "game_history", "achievements", "profiles"]}
