import yaml
import json
import os
from datetime import datetime
from crewai import Agent, Crew, Task, Process, LLM
from dotenv import load_dotenv
from crewai.tools import BaseTool
from pydantic import Field
from langchain_community.utilities import GoogleSerperAPIWrapper


load_dotenv()

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

# Required Additions for External Integration:
"""
1. Spoonacular API (Free Tier):
   - Needed for: Recipe database access
   - Setup: 
    - Register at spoonacular.com/food-api
    - Add API key to environment variables
    - Rate limit: 150 requests/day

"""


# Tools
search = GoogleSerperAPIWrapper()

class SearchTool(BaseTool):
    name: str = "Search"
    description: str = "Useful for search-based queries. Use this to find current information about markets, companies, and trends."
    search: GoogleSerperAPIWrapper = Field(default_factory=GoogleSerperAPIWrapper)

    def _run(self, query: str) -> str:
        """Execute the search query and return results"""
        try:
            return self.search.run(query)
        except Exception as e:
            return f"Error performing search: {str(e)}"

# AI Agents
input_processor = Agent(
    role="Dietary Pattern Analyzer",
    goal="Identify explicit and implicit nutritional constraints from user input",
    backstory="Specializes in detecting cultural preferences, food intolerances, and hidden dietary patterns",
    verbose=True,
    llm=llm,
    memory=True,
    tools=[],  # Add food database lookup tool if available
    system_prompt="Always ask clarifying questions about cooking time preferences"
)

nutrition_researcher = Agent(
    role="Precision Nutrition Engineer",
    goal="Calculate TDEE and create dynamic nutrient targets",
    backstory="Combines sports nutrition certification with clinical dietetics expertise",
    verbose=True,
    llm=llm,  # For precise calculations
    system_prompt="""Use latest NIH equations for metabolic calculations:
    - Mifflin-St Jeor for BMR
    - Harris-Benedict for activity adjustment
    - Always consider body composition goals"""
)

diet_planner = Agent(
    role="Culinary Nutrition Designer",
    goal="Create quick-prep meals using ONLY approved ingredients in authentic Italian style",
    backstory="Third-generation Italian chef specializing in 30-minute Mediterranean diets",
    verbose=True,
    llm=llm,
    allow_delegation=False,
    tools=[],  # Add Spoonacular API tool for recipes
    system_prompt="""Prioritize these cooking methods:
    1. One-pan meals 2. Sheet pan dinners 3. Instant pot recipes
    Maximum 5 ingredients per meal"""
)

plan_validator = Agent(
    role="Nutritional Compliance Auditor",
    goal="Ensure strict adherence to ALL constraints",
    backstory="Food safety inspector with nutrition certification",
    verbose=True,
    llm=llm,
    tools=[SearchTool()],  # Add nutrition analysis tool
    system_prompt="Check these in order: 1. Ingredient compliance 2. Prep time 3. Macro targets"
)

# Enhanced Task Definitions
analysis_task = Task(
    description="""Extract critical parameters:
    User Profile:
    - Age: {age}
    - Weight: {weight}kg
    - Height: {height}cm
    - Goal: {goal}
    - Food Preferences: {food_preferences}
    - Cultural Focus: Italian cuisine
    - Max Prep Time: 30 mins/meal
    
    Output format:
    - BMR/TDEE calculations
    - Macronutrient ranges
    - Flagged incompatible foods
    - Cultural adaptation plan""",
    agent=input_processor,
    expected_output="Structured JSON with metabolic data and constraint analysis"
)

nutrition_task = Task(
    description="""Create dynamic nutrition protocol:
    - Protein: 1.6-2.2g/kg based on activity level
    - Carb cycling for {g}
    - Mediterranean diet micronutrient focus
    - 30% caloric deficit/surplus based on goal
    - Strict Italian food alignment
    
    Required output:
    - Daily targets (energy, macros, fiber)
    - Meal timing schedule
    - Supplement recommendations""",
    agent=nutrition_researcher,
    expected_output="Table-based nutrition plan with Italian food mappings"
)

mealplan_task = Task(
    description="""Generate QUICK PREP Italian meal plan:
    - 7 days, 3 meals + 2 snacks
    - Max 30 mins active cooking time per meal
    - Use ONLY: {food_preferences}
    - Authentic regional Italian recipes
    - Include:
      * Step-by-step quick prep instructions
      * Pan/pot requirements
      * Batch cooking markers
      * Nutritional breakdown per meal
    
    Format: Markdown with cooking timeline""",
    agent=diet_planner,
    expected_output="Time-optimized meal plan with visual cooking guides"
)

validation_task = Task(
    description="""Perform strict quality check:
    1. Macro/micro compliance (±5%)
    2. Ingredient compliance (ZERO exceptions)
    3. Cultural authenticity
    4. Prep time constraints
    5. Meal variety score
    
    Output: Validation report with improvement checklist""",
    agent=plan_validator,
    expected_output="PDF-style audit report with pass/fail markers"
)


# CrewAI Processing Function
async def generate_meal_plan(user_inputs):
    crew = Crew(
        agents=[input_processor, nutrition_researcher, diet_planner, plan_validator],
        tasks=[analysis_task, nutrition_task, mealplan_task, validation_task],
        process=Process.hierarchical,
        verbose=True,
        memory=True
    )
    
    result = crew.kickoff(user_inputs)

    return result.output
    