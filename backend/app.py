from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from security import get_password_hash, verify_password
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.sessions import SessionMiddleware
import sqlite3
import os
import uuid
from fastapi import WebSocket, WebSocketDisconnect
import json
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
import logging
from agents import generate_meal_plan
import uvicorn

# Configuration
MEAL_PLANS_DIR = "data/meal_plans"
os.makedirs(MEAL_PLANS_DIR, exist_ok=True)

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware configuration
app.add_middleware(
    SessionMiddleware,
    secret_key=os.urandom(24).hex(),
    session_cookie="session_cookie",
    max_age=3600,  # 1 hour expiration
    same_site="Lax",
)

# Logger setup
logger = logging.getLogger(__name__)

# Pydantic models
class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    password: str

class MealPlanRequest(BaseModel):
    pass  # Define your actual request parameters here

def validate_password(password: str):
    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters"
        )
# Database initialization
@app.on_event("startup")
def startup_db():
    conn = sqlite3.connect("diet_planner.db")
    try:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS meal_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                file_path TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS foods (
                name TEXT NOT NULL,
                portion TEXT NOT NULL,
                carbs REAL NOT NULL,
                protein REAL NOT NULL,
                fat REAL NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()

# Dependency to get current user
async def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    conn = sqlite3.connect("diet_planner.db")
    try:
        c = conn.cursor()
        c.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": user[0], "username": user[1]}
    finally:
        conn.close()

# Helper functions
def save_meal_plan(content):
    """Save meal plan to file and return file path"""
    filename = f"{uuid.uuid4()}-{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
    filepath = os.path.join(MEAL_PLANS_DIR, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content.raw)
        return filepath
    except IOError as e:
        logger.error(f"Failed to save meal plan: {str(e)}")
        raise

# Routes
@app.post("/api/login")
async def login(user_data: UserLogin, request: Request):
    conn = sqlite3.connect("diet_planner.db")
    try:
        c = conn.cursor()
        c.execute("SELECT id, username, password_hash FROM users WHERE username = ?", 
                 (user_data.username,))
        user = c.fetchone()
        
        if not user or not verify_password(user_data.password, user[2]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        request.session["user_id"] = user[0]
        return {"message": "Logged in"}
    finally:
        conn.close()


@app.post("/api/register")
async def register(user_data: UserRegister):
    validate_password(user_data.password)
    conn = sqlite3.connect("diet_planner.db")
    try:
        c = conn.cursor()
        hashed_pw = get_password_hash(user_data.password)
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                 (user_data.username, hashed_pw))
        conn.commit()
        return {"message": "Registered"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username exists")
    finally:
        conn.close()


# Add WebSocket route
@app.websocket("/api/generate-plan-ws")
async def generate_plan_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        # Authenticate first
        auth = await websocket.receive_text()
        try:
            auth_data = json.loads(auth)
            user = await authenticate_user(auth_data)
        except Exception as e:
            await websocket.send_json({"error": "Authentication failed"})
            await websocket.close()
            return

        # Receive parameters
        params = await websocket.receive_json()
        
        # Generate meal plan with progress updates
        async def progress_callback(progress: float, message: str):
            await websocket.send_json({
                "type": "progress",
                "progress": progress,
                "message": message
            })
        
        try:
            result = await generate_meal_plan(
                params, 
                progress_callback=progress_callback
            )
            
            # Save to database
            file_path = save_meal_plan(result)
            conn = sqlite3.connect("diet_planner.db")
            try:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO meal_plans 
                    (user_id, date, file_path) 
                    VALUES (?, datetime('now'), ?)
                """, (user["id"], file_path))
                conn.commit()
                plan_id = c.lastrowid
                
                await websocket.send_json({
                    "type": "complete",
                    "id": plan_id,
                    "file_path": file_path
                })
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            await websocket.send_json({
                "type": "error",
                "message": "Meal plan generation failed"
            })
            
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()

async def authenticate_user(auth_data: dict):
    conn = sqlite3.connect("diet_planner.db")
    try:
        c = conn.cursor()
        c.execute("SELECT id, username, password_hash FROM users WHERE username = ?", 
                 (auth_data["username"],))
        user = c.fetchone()
        
        if not user or not verify_password(auth_data["password"], user[2]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        return {"id": user[0], "username": user[1]}
    finally:
        conn.close()

@app.get("/api/meal-plans/{id}")
async def get_meal_plan(
    id: int,
    current_user: dict = Depends(get_current_user)
):
    conn = sqlite3.connect("diet_planner.db")
    try:
        c = conn.cursor()
        c.execute("""
            SELECT file_path 
            FROM meal_plans 
            WHERE id = ? AND user_id = ?
        """, (id, current_user["id"]))
        result = c.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Plan not found")
            
        file_path = result[0]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"content": content}
        except FileNotFoundError:
            logger.error(f"Missing plan file: {file_path}")
            raise HTTPException(status_code=404, detail="Plan content unavailable")
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        conn.close()

@app.get("/api/food-db")
async def get_food_db():
    conn = sqlite3.connect("diet_planner.db")
    try:
        c = conn.cursor()
        c.execute("SELECT name, portion, carbs, protein, fat FROM foods")
        foods = [
            {
                "name": row[0],
                "portion": row[1],
                "carbs": row[2],
                "protein": row[3],
                "fat": row[4]
            } 
            for row in c.fetchall()
        ]
        return foods
    finally:
        conn.close()

@app.get("/api/meal-plans")
async def get_meal_plans(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect("diet_planner.db")
    try:
        c = conn.cursor()
        c.execute("SELECT id, date FROM meal_plans WHERE user_id = ?", (current_user["id"],))
        plans = [
            {"id": row[0], "date": row[1]}
            for row in c.fetchall()
        ]
        return plans
    finally:
        conn.close()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="localhost",
        port=5000,
        log_level="info",
        http="h11",
        timeout_keep_alive=40000
        )