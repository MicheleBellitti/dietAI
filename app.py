from flask import Flask, request, render_template
from crewai import Agent, Crew, Task, Process, LLM
import ollama
import json

app = Flask(__name__)

# Load food database
with open('food_database.json') as f:
    FOOD_DB = json.load(f)

llm = LLM("ollama/llama3.1:8b", base_url='http://localhost:11434')

# Enhanced Agent Definitions
input_processor = Agent(
    role="Nutrition Profile Analyst",
    goal="Extract key nutritional requirements and food preferences from user input",
    backstory="Expert in analyzing dietary needs and food restrictions",
    verbose=True,
    llm=llm,
    memory=True
)

nutrition_researcher = Agent(
    role="Nutrition Scientist",
    goal="Calculate precise nutritional targets based on user profile",
    backstory="PhD in nutritional science with expertise in diet planning",
    verbose=True,
    llm=llm,
    tools=[]
)

diet_planner = Agent(
    role="Master Chef Dietitian",
    goal="Create personalized meal plans using ONLY selected foods",
    backstory="Michelin-star chef with nutrition certification",
    verbose=True,
    llm=llm,
    allow_delegation=False
)

plan_validator = Agent(
    role="Diet Plan Quality Assurance",
    goal="Ensure meal plan strictly follows food preferences and nutritional goals",
    backstory="Detail-oriented nutrition auditor",
    verbose=True,
    llm=llm
)

# Enhanced Task Definitions
analysis_task = Task(
    description="""Analyze user profile:
    - Age: {age}
    - Weight: {current_weight}kg
    - Goal: {goal}
    - Activity Level: {routine}
    - Selected Foods: {food_preferences}
    Calculate BMR and TDEE using Mifflin-St Jeor equation.
    Identify nutritional requirements and constraints.""",
    agent=input_processor,
    expected_output="Structured JSON analysis of nutritional needs"
)

nutrition_task = Task(
    description="""Based on the analysis:
    - Calculate daily calorie target
    - Determine optimal macro split (protein/fat/carbs)
    - Set micronutrient goals
    - Strictly consider food preferences: {food_preferences}
    Create detailed nutritional guidelines.""",
    agent=nutrition_researcher,
    expected_output="Precision nutrition plan in JSON format"
)

mealplan_task = Task(
    description="""Create 7-day meal plan with:
    - 3 main meals + 2 snacks daily
    - Use ONLY these foods: {food_preferences}
    - Strict macro adherence
    - Italian cuisine focus
    - Include recipes and portion sizes
    - No unapproved ingredients!""",
    agent=diet_planner,
    expected_output="Markdown formatted meal plan with recipes"
)

validation_task = Task(
    description="""Verify meal plan:
    1. Only uses approved ingredients
    2. Meets nutritional targets
    3. Provides variety
    4. Practical preparation""",
    agent=plan_validator,
    expected_output="Validated meal plan with improvement suggestions"
)

# Configure Crew
crew = Crew(
    agents=[input_processor, nutrition_researcher, diet_planner, plan_validator],
    tasks=[analysis_task, nutrition_task, mealplan_task, validation_task],
    process=Process.sequential,
    verbose=True,
)

# Flask Routes
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', food_db=FOOD_DB)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Get selected foods from checkboxes
        selected_foods = {
            'vegetables': request.form.getlist('vegetables'),
            'fruits': request.form.getlist('fruits'),
            'proteins': request.form.getlist('proteins'),
            'carbs': request.form.getlist('carbs'),
            'fats': request.form.getlist('fats')
        }
        
        # Get other form data
        user_inputs = {
            'age': int(request.form['age']),
            'current_weight': float(request.form['current_weight']),
            'height': float(request.form['height']),
            'goal': request.form['goal'],
            'kg_per_week': float(request.form.get('kg_per_week', 0.5)),
            'routine': request.form['routine'],
            'food_preferences': selected_foods
        }

        # Execute planning process
        result = crew.kickoff(inputs=user_inputs)
        return render_template('result.html', 
                             diet_plan=result,
                             selected_foods=selected_foods)
    
    except Exception as e:
        return render_template('error.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=True)