import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';
import Loader from '@/components/Loader';
import Button from '@/components/Button';
import Card from '@/components/Card';

interface FoodItem {
  name: string;
  category: string;
  portion: string;
  carbs: number;
  protein: number;
  fat: number;
}

export default function GeneratePlan() {
  const router = useRouter();
  const [foods, setFoods] = useState<{ [category: string]: FoodItem[] }>({});
  const [selectedFoods, setSelectedFoods] = useState<{ [category: string]: string[] }>({});
  const [formData, setFormData] = useState({
    age: '',
    weight: '',
    height: '',
    goal: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [taskId, setTaskId] = useState<string | null>(null);

  const fetchFoods = useCallback(async () => {
    try {
      const res = await fetch('/api/food-db');
      if (!res.ok) throw new Error('Failed to load food options');
      
      const data: FoodItem[] = await res.json();
      const grouped = data.reduce((acc, item) => {
        if (!acc[item.category]) acc[item.category] = [];
        acc[item.category].push(item);
        return acc;
      }, {} as { [key: string]: FoodItem[] });
      
      setFoods(grouped);
      setSelectedFoods(
        Object.keys(grouped).reduce((acc, category) => ({
          ...acc,
          [category]: []
        }), {})
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load food options');
    }
  }, []);

  useEffect(() => {
    fetchFoods();
  }, [fetchFoods]);

  const handleFoodToggle = (category: string, food: string) => {
    setSelectedFoods(prev => ({
      ...prev,
      [category]: prev[category].includes(food) 
        ? prev[category].filter(f => f !== food)
        : [...prev[category], food]
    }));
  };

  const checkTaskStatus = useCallback(async (taskId: string) => {
    try {
      const res = await fetch(`/api/tasks/${taskId}`);
      if (!res.ok) throw new Error('Status check failed');
      
      const data = await res.json();
      
      if (data.status === 'completed') {
        router.push(`/plan/${data.result.plan_id}`);
      } else if (data.status === 'failed') {
        setError(data.error || 'Meal plan generation failed');
        setLoading(false);
      }
    } catch (err) {
      setError('Failed to check task status');
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    if (!taskId || !loading) return;

    const interval = setInterval(() => checkTaskStatus(taskId), 2000);
    return () => clearInterval(interval);
  }, [taskId, loading, checkTaskStatus]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/generate-meal-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          age: Number(formData.age),
          weight: Number(formData.weight),
          height: Number(formData.height),
          goal: formData.goal,
          food_preferences: selectedFoods
        })
      });

      if (!res.ok) throw new Error('Failed to start generation');
      
      const data = await res.json();
      setTaskId(data.task_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submission failed');
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-4xl font-bold mb-8 text-gray-800">Create Your Meal Plan</h1>
      
      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Age</label>
            <input
              type="number"
              value={formData.age}
              onChange={(e) => setFormData({ ...formData, age: e.target.value })}
              className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              min="1"
              required
            />
          </div>
          
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Weight (kg)</label>
            <input
              type="number"
              value={formData.weight}
              onChange={(e) => setFormData({ ...formData, weight: e.target.value })}
              className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              min="1"
              step="0.1"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Height (cm)</label>
            <input
              type="number"
              value={formData.height}
              onChange={(e) => setFormData({ ...formData, height: e.target.value })}
              className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              min="1"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Goal</label>
            <input
              type="text"
              value={formData.goal}
              onChange={(e) => setFormData({ ...formData, goal: e.target.value })}
              className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="e.g., Lose weight, Build muscle"
              required
            />
          </div>

        </div>

        <Card className="p-6 bg-white rounded-xl shadow-sm">
          {Object.entries(foods).map(([category, items]) => (
            <div key={category} className="mb-8">
              <h3 className="text-lg font-medium text-gray-700 mb-4 capitalize">
                {category.replace('_', ' ')}
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {items.map((food) => (
                  <label 
                    key={food.name}
                    className="flex items-center p-3 space-x-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedFoods[category]?.includes(food.name) || false}
                      onChange={() => handleFoodToggle(category, food.name)}
                      className="h-5 w-5 text-green-600 rounded focus:ring-green-500"
                    />
                    <span className="text-gray-700">{food.name}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </Card>

        <div className="space-y-4">
          <Button
            type="submit"
            disabled={loading}
            className="w-full py-4 text-lg font-semibold"
          >
            {loading ? (
              <div className="flex items-center justify-center gap-2">
                <Loader />
                Generating Plan...
              </div>
            ) : (
              'Generate My Plan'
            )}
          </Button>

          {error && (
            <div className="p-4 bg-red-50 text-red-700 rounded-lg text-center">
              {error}
            </div>
          )}
        </div>
      </form>
    </div>
  );
}