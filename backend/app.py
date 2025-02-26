from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user
import sqlite3
from agents import generate_meal_plan  # Existing logic

app = Flask(__name__)
app.secret_key = str(hash("kekkodesu"))

CORS(app) 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect("diet_planner.db")
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return User(user[0], user[1]) if user else None

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    conn = sqlite3.connect("diet_planner.db")
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE username = ?", (data["username"],))
    user = c.fetchone()
    if user:
        login_user(User(user[0], user[1]))
        return jsonify({"message": "Logged in"}), 200
    return jsonify({"error": "Invalid username"}), 401

@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    conn = sqlite3.connect("diet_planner.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username) VALUES (?)", (data["username"],))
        conn.commit()
        return jsonify({"message": "Registered"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username exists"}), 400
    finally:
        conn.close()

@app.route("/api/food-db", methods=["GET"])
def get_food_db():
    conn = sqlite3.connect("diet_planner.db")
    c = conn.cursor()
    c.execute("SELECT name, category FROM foods")
    foods = [{"name": row[0], "category": row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(foods)

@app.route("/api/generate-plan", methods=["POST"])
@login_required
def generate_plan():
    data = request.json
    meal_plan = generate_meal_plan(data)  # Existing logic
    conn = sqlite3.connect("diet_planner.db")
    c = conn.cursor()
    c.execute("INSERT INTO meal_plans (user_id, date, plan_content) VALUES (?, datetime('now'), ?)",
              (current_user.id, meal_plan))
    conn.commit()
    plan_id = c.lastrowid
    conn.close()
    return jsonify({"id": plan_id, "plan": meal_plan}), 201

@app.route("/api/meal-plans", methods=["GET"])
@login_required
def get_meal_plans():
    conn = sqlite3.connect("diet_planner.db")
    c = conn.cursor()
    c.execute("SELECT id, date FROM meal_plans WHERE user_id = ?", (current_user.id,))
    plans = [{"id": row[0], "date": row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(plans)

@app.route("/api/meal-plans/<int:id>", methods=["GET"])
@login_required
def get_meal_plan(id):
    conn = sqlite3.connect("diet_planner.db")
    c = conn.cursor()
    c.execute("SELECT plan_content FROM meal_plans WHERE id = ? AND user_id = ?", (id, current_user.id))
    plan = c.fetchone()
    conn.close()
    return jsonify({"plan": plan[0]}) if plan else jsonify({"error": "Not found"}), 404

if __name__ == "__main__":
    app.run(port=5000, debug=True)