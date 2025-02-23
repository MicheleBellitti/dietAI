# Run with: solara run frontend.py

import solara as sl
import httpx
import json
from typing import Dict, List

from solara.hooks import use_reactive
from pathlib import Path

# Load CSS
css_path = Path(__file__).parent / "style.css"
sl.Style(css_path)


# Add reactive variables for task tracking
task_id = sl.reactive(None)
status = sl.reactive("Not started")

# Load food database
with open('food_database.json') as f:
    FOOD_DB = json.load(f)

# Reactive state
age = sl.reactive("")
height = sl.reactive("")
weight = sl.reactive("")
body_fat = sl.reactive("16")
goal = sl.reactive("lose weight")
kg_per_week = sl.reactive("0.5")
routine = sl.reactive("sedentary")
selected_foods = sl.reactive({"vegetables": [], "fruits": [], "proteins": [], "carbs": [], "fats": []})
diet_plan = sl.reactive("")
loading = sl.reactive(False)
error = sl.reactive("")

import solara as sl
from typing import List, Dict

@sl.component
def FoodSelector(category: str, items: List[Dict]):

    def toggle_food(food_name: str, selected: bool):
        current = selected_foods.value[category].copy()
        if selected:
            current.append(food_name)
        else:
            current.remove(food_name)
        selected_foods.set({**selected_foods.value, category: current})

    with sl.Card(title=category.capitalize()):
        with sl.GridFixed(columns=4):
            for item in items:
                selected = item["name"] in selected_foods.value[category]
                sl.Checkbox(
                    label=f"{item['name']} ({item['portion']})",
                    value=selected,
                    on_value=lambda val, item=item: toggle_food(item["name"], val)
                )
def BiometricForm():
    with sl.Card("Personal Information"):
        sl.InputFloat("Age", value=age)
        sl.InputFloat("Height (cm)", value=height)
        sl.InputFloat("Weight (kg)", value=weight)
        sl.InputFloat("Body Fat %", value=body_fat)
        
        with sl.Row():
            sl.Select("Goal", value=goal, values=["lose weight", "gain muscle", "maintain"])
            sl.Select("Activity Level", value=routine, values=[
                "sedentary", "lightly active", "moderately active", "very active"
            ])
            sl.InputFloat("Weekly Target (kg)", value=kg_per_week)

def ResultDisplay():
    if diet_plan.value:
        with sl.Card("Your Personalized Diet Plan"):
            sl.Markdown(diet_plan.value)
            sl.Button("New Plan", on_click=lambda: diet_plan.set(""))

@sl.component
def Page():
    sl.lab.ThemeToggle()
    with sl.Column(style={"max-width": "1200px", "margin": "0 auto"}):
        sl.Title("🍝 Italian Diet Planner")
        
        if error.value:
            sl.Error(error.value)
        
        if loading.value:
            with sl.Row(justify="center"):
                sl.SpinnerSolara(size="100px", color_back="Yellow", color_front="Lime")
                sl.Text("Sending request...")
        elif task_id.value:
            with sl.Column():
                sl.Text("Your diet plan is being generated...")
                TaskStatus()
        elif diet_plan.value:
            ResultDisplay()
        else:
            BiometricForm()
            with sl.Card("Food Preferences"):
                for category, items in FOOD_DB.items():
                    if category in ["vegetables", "fruits", "proteins", "carbs", "fats"]:
                        FoodSelector(category, items)
            with sl.Row(justify="center"):
                sl.Button("Generate Plan",
                          on_click=generate_plan,
                          disabled=loading.value or not all([age.value, height.value, weight.value]),
                          classes=["bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"])
def generate_plan():
    loading.set(True)
    error.set("")
    try:
        # Validate and convert inputs
        try:
            age_val = int(age.value) if age.value else None
            height_val = float(height.value) if height.value else None
            weight_val = float(weight.value) if weight.value else None
            body_fat_val = float(body_fat.value) if body_fat.value else 25.0
            kg_per_week_val = float(kg_per_week.value) if kg_per_week.value else 0.5
        except ValueError:
            error.set("Please ensure all numeric inputs are valid numbers.")
            return

        if not all([age_val, height_val, weight_val]):
            error.set("Age, Height, and Weight are required fields.")
            return

        response = httpx.post(
            "http://localhost:5000/api/generate",
            json={
                "age": age_val,
                "height": height_val,
                "current_weight": weight_val,
                "body_fat": body_fat_val,
                "goal": goal.value,
                "kg_per_week": kg_per_week_val,
                "routine": routine.value,
                "food_preferences": selected_foods.value
            },
        )

        if response.status_code == 202:
            task_id.set(response.json()['task_id'])
            status.set('Pending')
        else:
            error.set(f"Backend error: {response.text}")
    except httpx.RequestError as e:
        error.set(f"Connection error: {str(e)}")
    except Exception as e:
        error.set(f"Unexpected error: {str(e)}")
    finally:
        loading.set(False)
        
def check_status():
    if task_id.value:
        try:
            response = httpx.get(f"http://localhost:5000/api/status/{task_id.value}")
            data = response.json()
            status.set(data['status'])
            if data['status'] == 'Complete':
                diet_plan.set(data['result']['plan'])
                task_id.set(None)
        except Exception as e:
            error.set(f"Error checking status: {str(e)}")
            
@sl.component
def TaskStatus():
    if task_id.value:
        use_reactive(check_status, 30000)  # Check every 30 seconds
        sl.Text(f"Current status: {status.value}")