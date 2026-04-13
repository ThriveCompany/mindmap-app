# Guess Authentication System

A clean, production-ready authentication system for the Guess web app.

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Backend**: Python with FastAPI
- **Database**: PostgreSQL with SQLAlchemy
- **Authentication**: JWT with bcrypt hashing

## Project Structure

```
guess/
├── backend/
│   ├── main.py          # FastAPI app
│   ├── models.py        # SQLAlchemy models
│   ├── auth.py          # Authentication utilities
│   ├── requirements.txt # Python dependencies
│   └── .env             # Environment variables
└── frontend/
    ├── signup.html      # Signup page
    ├── login.html       # Login page
    ├── dashboard.html   # Protected dashboard
    ├── styles.css       # Dark theme styles
    └── auth.js          # Frontend authentication logic
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL
- Node.js (for serving frontend, optional)

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up PostgreSQL database:
   - Create a database named `guess_db`
   - Update `.env` with your database credentials:
     ```
     DATABASE_URL=postgresql://username:password@localhost/guess_db
     SECRET_KEY=your-secret-key-here
     ```

4. Run the backend:
   ```bash
   uvicorn main:app --reload
   ```

   The API will be available at `http://localhost:8000`

### 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Serve the frontend (using Python's built-in server):
   ```bash
   python -m http.server 3000
   ```

   Or use any static file server. The frontend will be available at `http://localhost:3000`

### 3. Testing

1. Open `http://localhost:3000/signup.html` in your browser
2. Sign up with a username and password
3. Login with the same credentials
4. You should be redirected to the dashboard

## API Endpoints

- `POST /register` - Register a new user
- `POST /login` - Login and get JWT token
- `GET /me` - Get current user info (protected)

## Security Features

- Password hashing with bcrypt
- JWT token authentication
- Protected routes
- Input validation