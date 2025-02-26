import sqlite3

def init_db():
    conn = sqlite3.connect("diet_planner.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE)")
    c.execute("CREATE TABLE IF NOT EXISTS foods (id INTEGER PRIMARY KEY, name TEXT, category TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS meal_plans (id INTEGER PRIMARY KEY, user_id INTEGER, date TEXT, plan_content TEXT, FOREIGN KEY(user_id) REFERENCES users(id))")
    conn.commit()
    conn.close()