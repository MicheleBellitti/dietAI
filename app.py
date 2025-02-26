import uuid
from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
import json
import yaml
import os
from datetime import datetime
from agents import generate_meal_plan

app = Flask(__name__)

# Load food database
with open('food_database.json') as f:
    FOOD_DB = json.load(f)

# Load Configuration
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

USER_DB_PATH = config["storage"]["user_db"]
MEAL_PLANS_DIR = config["storage"]["meal_plans_dir"]

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, username):
        self.username = username

    def get_id(self):
        return self.username

@login_manager.user_loader
def load_user(username):
    data = read_json(USER_DB_PATH)
    user_record = next((u for u in data["users"] if u["username"] == username), None)
    return User(username=user_record["username"]) if user_record else None

def read_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)
from flask import render_template_string
import markdown

@app.route('/plan/<filename>')
def show_plan(filename):
    # Load MD file from plans directory
    with open(f'meal_plans/plans/{filename}.md', 'r') as f:
        md_content = f.read()
    
    # Convert Markdown to HTML
    html_content = markdown.markdown(md_content)
    
    # Render with template
    return render_template('result.html', 
                         content=html_content,
                         filename=filename)
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", food_db=FOOD_DB)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        data = read_json(USER_DB_PATH)
        user_record = next((u for u in data["users"] if u["username"] == username), None)

        if user_record:
            user = User(username=user_record["username"])
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid username")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = current_user.get_id()
    meal_plans_meta = read_json(f"{MEAL_PLANS_DIR}/{user_id}.json")
    meal_plans_meta = meal_plans_meta if meal_plans_meta else {}
    meal_plans = {}
    for id in meal_plans_meta.keys():
        # meal plans are stored in .md files
        meal_plans[id] = {"plan": open(meal_plans_meta[id]["plan_path"], "r").read()}
    return render_template("dashboard.html", meal_plans=meal_plans)

@app.route("/generate", methods=["POST"])
@login_required
def generate():
    selected_foods = {
        "vegetables": request.form.getlist("vegetables"),
        "fruits": request.form.getlist("fruits"),
        "proteins": request.form.getlist("proteins"),
        "carbs": request.form.getlist("carbs"),
        "fats": request.form.getlist("fats"),
    }

    user_inputs = {
        "age": int(request.form["age"]),
        "current_weight": float(request.form["weight"]),
        "height": float(request.form["height"]),
        "goal": request.form["goal"],
        "food_preferences": selected_foods,
    }
    crew =  generate_meal_plan(user_inputs)
    meal_plan = crew.model_dump_json()
    
    user_id = current_user.get_id()
    meal_plan_data = read_json(f"{MEAL_PLANS_DIR}/{user_id}.json")
    new_id = uuid.uuid4().hex
    meal_plan_data[f'{new_id}'] = {"date": str(datetime.now()), "plan_path": f"{MEAL_PLANS_DIR}/plans/{new_id}.md"}
    write_json(f"{MEAL_PLANS_DIR}/{user_id}.json", meal_plan_data)
    with open(f"{MEAL_PLANS_DIR}/plans/{new_id}.md", "w") as f:
        f.write(meal_plan)

    return render_template("result.html", diet_plan=meal_plan)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        data = read_json(USER_DB_PATH)
        if next((u for u in data["users"] if u["username"] == username), None):
            flash("Username already exists")
        else:
            data["users"].append({"username": username})
            write_json(USER_DB_PATH, data)
            return redirect(url_for("login"))
    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)
