from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import os
from dotenv import load_dotenv

from .models import Base, User, Game
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
        print("Database tables created successfully")
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
    wins: int
    losses: int
    games_played: int
    win_rate: float

class GameCreate(BaseModel):
    min_range: int = 1
    max_range: int = 100
    user_number: int

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
def read_users_me(current_user: User = Depends(get_current_user)):
    wins = current_user.wins
    losses = current_user.losses
    games_played = current_user.games_played
    win_rate = (wins / games_played * 100) if games_played > 0 else 0.0  # type: ignore
    return {
        "id": current_user.id,
        "username": current_user.username,
        "wins": wins,
        "losses": losses,
        "games_played": games_played,
        "win_rate": round(win_rate, 2)  # type: ignore
    }

@app.post("/games", response_model=GameResponse)
def create_game(game: GameCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not (game.min_range <= game.user_number <= game.max_range):
        raise HTTPException(status_code=400, detail="User number must be within range")
    import random
    system_number = random.randint(game.min_range, game.max_range)
    db_game = Game(
        user_id=current_user.id,
        user_number=game.user_number,
        system_number=system_number,
        min_range=game.min_range,
        max_range=game.max_range,
        current_min=game.min_range,
        current_max=game.max_range
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
    status = game.status
    if status != "active":  # type: ignore
        raise HTTPException(status_code=400, detail="Game is not active")
    current_min = game.current_min
    current_max = game.current_max
    if not (current_min <= guess_data.guess <= current_max):  # type: ignore
        raise HTTPException(status_code=400, detail="Guess must be within current range")
    
    messages = [f"Is your number {guess_data.guess}?"]
    system_number = game.system_number
    if guess_data.guess < system_number:  # type: ignore
        messages.append("Higher ⬆️")
        game.current_min = guess_data.guess + 1  # type: ignore
    elif guess_data.guess > system_number:  # type: ignore
        messages.append("Lower ⬇️")
        game.current_max = guess_data.guess - 1  # type: ignore
    else:
        messages.append("Yes! You win 🎉")
        game.status = "won"  # type: ignore
        current_user.wins = current_user.wins + 1  # type: ignore
        current_user.games_played = current_user.games_played + 1  # type: ignore
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
    
    # Check if user lost (if current_min > current_max, but since system_number is within, it shouldn't happen)
    if game.current_min > game.current_max:  # type: ignore
        messages.append("Impossible! You lose 😢")
        game.status = "lost"  # type: ignore
        current_user.losses = current_user.losses + 1  # type: ignore
        current_user.games_played = current_user.games_played + 1  # type: ignore
    
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

@app.get("/version")
def version():
    return {"version": "1.0", "cors": "fixed", "origins": ["https://mindmap-app-jade-pi.vercel.app"]}
