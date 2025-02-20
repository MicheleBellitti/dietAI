import unittest
from unittest.mock import patch
from app import app, crew

class TestDietPlanner(unittest.TestCase):
    """
    Test cases for the diet planner application.
    Covers crew execution, Flask routes, and template rendering.
    """

    def setUp(self):
        """
        Set up the test client for Flask.
        This runs before each test case.
        """
        self.app = app.test_client()
        self.app.testing = True

    @patch('ollama.generate')
    def test_crew_execution(self, mock_generate):
        """
        Test that the AI crew executes all tasks correctly.
        Mocks Ollama responses to ensure consistent output.
        """
        # Mock the responses from Ollama for each agent
        mock_generate.side_effect = [
            {"response": "Mock summary"},
            {"response": "Mock guidelines"},
            {"response": "Mock diet plan"}
        ]

        # Simulate user inputs
        user_inputs = {
            "vegetables": ["broccoli", "spinach"],
            "fruits": ["apples", "bananas"],
            "other_foods": ["chicken", "rice"],
            "goal": "lose weight",
            "kg_per_week": 0.5,
            "age": 30,
            "current_weight": 80.0,
            "sex": "male",
            "routine": "sedentary"
        }

        # Run the crew with the user inputs
        result = crew.kickoff(inputs={"user_inputs": user_inputs})

        # Check if the final output is the mock diet plan
        self.assertEqual(result, "Mock diet plan")

    def test_index_get(self):
        """
        Test GET request to the index page.
        Ensures the input form is rendered correctly.
        """
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Diet Planner', response.data)

    @patch('ollama.generate')
    def test_index_post(self, mock_generate):
        """
        Test POST request to the index page.
        Simulates form submission, checks that the crew is executed,
        and ensures the result page displays the diet plan.
        """
        # Mock the responses from Ollama for each agent
        mock_generate.side_effect = [
            {"response": "Mock summary"},
            {"response": "Mock guidelines"},
            {"response": "Mock diet plan"}
        ]

        # Simulate POST request with sample form data
        response = self.app.post('/', data={
            'vegetables': 'broccoli,spinach',
            'fruits': 'apples,bananas',
            'other_foods': 'chicken,rice',
            'goal': 'lose weight',
            'kg_per_week': '0.5',
            'age': '30',
            'current_weight': '80',
            'sex': 'male',
            'routine': 'sedentary'
        })

        # Check if the response is 200 and contains the mock diet plan
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Mock diet plan', response.data)

if __name__ == '__main__':
    unittest.main()