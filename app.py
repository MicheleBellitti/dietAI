from flask import Flask, request, render_template
from crewai import Agent, Crew, Task, Process
import ollama

app = Flask(__name__)

# Function to use Ollama's local language model
def llm(prompt):
    response = ollama.generate(model="llama3", prompt=prompt)
    return response["response"]

# Define the AI agents
input_processor = Agent(
    role="Input Processor",
    goal="Turn user inputs into a clear summary.",
    backstory="You excel at summarizing user details into simple descriptions.",
    verbose=True,
    llm=llm
)

nutrition_researcher = Agent(
    role="Nutrition Researcher",
    goal="Suggest nutritional guidelines based on a user’s profile.",
    backstory="You’re a nutrition expert who knows dietary needs.",
    verbose=True,
    llm=llm
)

diet_planner = Agent(
    role="Diet Planner",
    goal="Make a weekly diet plan using guidelines and food preferences.",
    backstory="You craft personalized meal plans for users.",
    verbose=True,
    llm=llm
)

# Define tasks for the agents
task1 = Task(
    description="Summarize the user’s inputs into a paragraph with their profile and food preferences.",
    agent=input_processor,
    expected_output="A paragraph about the user’s profile and preferences."
)

task2 = Task(
    description="Use the summary to suggest daily nutritional guidelines, like calories and macronutrients.",
    agent=nutrition_researcher,
    expected_output="Nutritional guidelines as a string."
)

task3 = Task(
    description="Create a weekly diet plan with daily meals based on the guidelines and preferred foods.",
    agent=diet_planner,
    expected_output="A weekly diet plan with meals for each day."
)

# Set up the crew to run tasks in sequence
crew = Crew(
    agents=[input_processor, nutrition_researcher, diet_planner],
    tasks=[task1, task2, task3],
    process=Process.sequential,
    verbose=True
)

# Flask routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get form data
        vegetables = request.form['vegetables'].split(',')
        fruits = request.form['fruits'].split(',')
        other_foods = request.form['other_foods'].split(',')
        goal = request.form['goal']
        kg_per_week = float(request.form['kg_per_week']) if request.form['kg_per_week'] else None
        age = int(request.form['age'])
        current_weight = float(request.form['current_weight'])
        sex = request.form['sex']
        routine = request.form['routine']

        # Organize inputs into a dictionary
        user_inputs = {
            "vegetables": vegetables,
            "fruits": fruits,
            "other_foods": other_foods,
            "goal": goal,
            "kg_per_week": kg_per_week,
            "age": age,
            "current_weight": current_weight,
            "sex": sex,
            "routine": routine
        }

        # Run the crew with user inputs
        result = crew.kickoff(inputs={"user_inputs": user_inputs})

        # Show the diet plan
        return render_template('result.html', diet_plan=result)

    # Show the input form
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)