from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from security import get_password_hash, verify_password
from starlette.middleware.sessions import SessionMiddleware
import sqlite3
import os
import uuid
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
    age: int
    weight: float
    height: int
    goal: str
    food_preferences: dict

class TaskStatusResponse(BaseModel):
    status: str
    result: Optional[dict]
    error: Optional[str]

# Database initialization

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
        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
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
def save_meal_plan(content: str) -> str:
    """Save meal plan to file and return file path"""
    filename = f"{uuid.uuid4()}-{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
    filepath = os.path.join(MEAL_PLANS_DIR, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
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
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters"
        )
        
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

@app.post("/api/generate-meal-plan", response_model=dict)
async def create_meal_plan_task(
    request_data: MealPlanRequest,
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    task_id = str(uuid.uuid4())
    conn = sqlite3.connect("diet_planner.db")
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO tasks (id, user_id, status)
            VALUES (?, ?, 'pending')
        """, (task_id, current_user["id"]))
        conn.commit()
    finally:
        conn.close()
    
    background_tasks.add_task(
        process_meal_plan_task,
        task_id,
        current_user["id"],
        request_data.dict()
    )
    return {"task_id": task_id, "status": "pending"}

@app.get("/api/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    conn = sqlite3.connect("diet_planner.db")
    try:
        c = conn.cursor()
        c.execute("""
            SELECT status, result, error
            FROM tasks
            WHERE id = ? AND user_id = ?
        """, (task_id, current_user["id"]))
        task = c.fetchone()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        return {
            "status": task[0],
            "result": json.loads(task[1]) if task[1] else None,
            "error": task[2]
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid task result format")
    finally:
        conn.close()

async def process_meal_plan_task(task_id: str, user_id: int, params: dict):
    conn = sqlite3.connect("diet_planner.db")
    try:
        # Simulate meal plan generation
        result = await generate_meal_plan(params)
        file_path = save_meal_plan(result)
        
        c = conn.cursor()
        c.execute("""
            INSERT INTO meal_plans (user_id, date, file_path)
            VALUES (?, datetime('now'), ?)
        """, (user_id, file_path))
        plan_id = c.lastrowid
        conn.commit()
        
        c.execute("""
            UPDATE tasks 
            SET status = 'completed',
                result = ?
            WHERE id = ?
        """, (json.dumps({"plan_id": plan_id, "file_path": file_path}), task_id))
        conn.commit()
        
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        c.execute("""
            UPDATE tasks 
            SET status = 'failed',
                error = ?
            WHERE id = ?
        """, (str(e), task_id))
        conn.commit()
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
    finally:
        conn.close()

@app.get("/api/food-db")
async def get_food_db():
    conn = sqlite3.connect("diet_planner.db")
    try:
        c = conn.cursor()
        c.execute("SELECT name, portion, carbs, protein, fat FROM foods")
        return [
            {
                "name": row[0],
                "portion": row[1],
                "carbs": row[2],
                "protein": row[3],
                "fat": row[4]
            }
            for row in c.fetchall()
        ]
    finally:
        conn.close()

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=5000)