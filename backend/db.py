import sqlite3
import json

def init_db():
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


def populate_db():
    conn = sqlite3.connect("diet_planner.db")
    c = conn.cursor()
    # Insert data from food_database.json
    with open("../food_database.json", "r") as f:
        foods = json.load(f)
        #print(foods)
        for macro_food, data in foods.items():
            for food in data:
                print(food)
                c.execute("INSERT INTO foods (name, portion, carbs, protein, fat) VALUES (?, ?, ?, ?, ?)", (food["name"], food["portion"], food["carbs"], food["protein"], food["fat"]))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    populate_db()
#     (login.current_user.id, json.dumps(meal_plan))
#     conn.commit()
#     plan_id = c.lastrowid
#     conn.close()
#     return jsonify({"id": plan_id, "plan": meal_plan}), 201