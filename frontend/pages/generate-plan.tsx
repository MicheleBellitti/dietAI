// pages/generate-plan.tsx
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

export default function GeneratePlan() {
  const [foods, setFoods] = useState<{ [category: string]: string[] }>({});
  const [selectedFoods, setSelectedFoods] = useState<{ [category: string]: string[] }>({});
  const [age, setAge] = useState('');
  const [weight, setWeight] = useState('');
  const [height, setHeight] = useState('');
  const [goal, setGoal] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    const fetchFoods = async () => {
      try {
        const res = await fetch('/api/food-db', { credentials: 'include' });
        if (res.status === 401) {
          router.push('/login');
          return;
        }
        if (res.ok) {
          const data = await res.json();
          // Assuming data is an array of { name: string, category: string }
          const grouped = data.reduce((acc: { [key: string]: string[] }, food: { name: string; category: string }) => {
            if (!acc[food.category]) acc[food.category] = [];
            acc[food.category].push(food.name);
            return acc;
          }, {});
          setFoods(grouped);
          const initialSelected = Object.keys(grouped).reduce((acc, category) => {
            acc[category] = [];
            return acc;
          }, {} as { [key: string]: string[] });
          setSelectedFoods(initialSelected);
        } else {
          setError('Failed to load food options.');
        }
      } catch (err) {
        setError('An error occurred while fetching food options.');
      }
    };
    fetchFoods();
  }, [router]);

  const handleFoodToggle = (category: string, food: string) => {
    setSelectedFoods((prev) => {
      const newSelected = { ...prev };
      if (newSelected[category].includes(food)) {
        newSelected[category] = newSelected[category].filter((f) => f !== food);
      } else {
        newSelected[category].push(food);
      }
      return newSelected;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/generate-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ age, weight, height, goal, food_preferences: selectedFoods }),
        credentials: 'include',
      });

      if (res.status === 401) {
        router.push('/login');
        return;
      }

      if (res.ok) {
        const data = await res.json();
        router.push(`/plan/${data.id}`);
      } else {
        setError('Failed to generate meal plan.');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Generate Meal Plan</h1>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input
            type="number"
            value={age}
            onChange={(e) => setAge(e.target.value)}
            placeholder="Age"
            className="p-2 border rounded w-full focus:outline-none focus:ring-2 focus:ring-green-500"
            required
          />
          <input
            type="number"
            value={weight}
            onChange={(e) => setWeight(e.target.value)}
            placeholder="Weight (kg)"
            className="p-2 border rounded w-full focus:outline-none focus:ring-2 focus:ring-green-500"
            required
          />
          <input
            type="number"
            value={height}
            onChange={(e) => setHeight(e.target.value)}
            placeholder="Height (cm)"
            className="p-2 border rounded w-full focus:outline-none focus:ring-2 focus:ring-green-500"
            required
          />
          <input
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="Goal (e.g., lose weight)"
            className="p-2 border rounded w-full focus:outline-none focus:ring-2 focus:ring-green-500"
            required
          />
        </div>
        <div>
          <h2 className="text-xl font-semibold mb-4">Select Your Food Preferences</h2>
          {Object.entries(foods).map(([category, items]) => (
            <div key={category} className="mb-4">
              <h3 className="text-lg font-medium capitalize">{category}</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2">
                {items.map((food) => (
                  <label key={food} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={selectedFoods[category]?.includes(food) || false}
                      onChange={() => handleFoodToggle(category, food)}
                      className="h-4 w-4 text-green-500"
                    />
                    <span>{food}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
        <button
          type="submit"
          disabled={loading}
          className={`w-full p-2 text-white rounded ${
            loading ? 'bg-green-400 cursor-not-allowed' : 'bg-green-500 hover:bg-green-600'
          }`}
        >
          {loading ? 'Generating...' : 'Generate Plan'}
        </button>
        {error && <p className="text-red-500 text-center">{error}</p>}
      </form>
    </div>
  );
}