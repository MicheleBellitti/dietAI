import yaml
import json
import os
from datetime import datetime
from crewai import Agent, Crew, Task, Process, LLM
import ollama

# Load Configuration
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

MODEL_PROVIDER = config["ai_model"]["provider"]
MODEL_NAME = config["ai_model"]["model_name"]
TEMPERATURE = config["ai_model"]["temperature"]
# MAX_TOKENS = config["ai_model"]["max_tokens"]

# Ensure meal plans directory exists
MEAL_PLANS_DIR = config["storage"]["meal_plans_dir"]
os.makedirs(MEAL_PLANS_DIR, exist_ok=True)

# Setup LLM
llm = LLM(MODEL_NAME)

# AI Agents
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

# Task Definitions
analysis_task = Task(
    description="""Analyze user profile:
    - Age: {age}
    - Weight: {weight}kg
    - Goal: {goal}
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
    expected_output="Precise nutrition plan"
)

mealplan_task = Task(
    description="""Create a 7-day meal plan:
    - 3 meals + 2 snacks daily
    - Use ONLY these foods: {food_preferences}
    - Strict macro adherence
    - Italian cuisine focus
    - Include recipes and portion sizes""",
    agent=diet_planner,
    expected_output="Structured Markdown meal plan"
)

validation_task = Task(
    description="Verify meal plan for quality and adherence to goals.",
    agent=plan_validator,
    expected_output="Validated meal plan with improvement suggestions"
)

# CrewAI Processing Function
async def generate_meal_plan(user_inputs, progress_callback: callable):
    crew = Crew(
        agents=[input_processor, nutrition_researcher, diet_planner, plan_validator],
        tasks=[analysis_task, nutrition_task, mealplan_task, validation_task],
        verbose=True,
        memory=True
    )
    await progress_callback(0.1, "Initializing...")
    
    await progress_callback(0.5, "Generating recipes...")
    result = crew.kickoff(user_inputs)

    return result.output
    