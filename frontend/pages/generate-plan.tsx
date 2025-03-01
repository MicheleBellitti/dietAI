// pages/generate-plan.tsx
import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';
import Loader from '@/components/Loader';
import Button from '@/components/Button';
import Card  from '@/components/Card'; // Assume you have a Card component

export default function GeneratePlan() {
  const [foods, setFoods] = useState<{ [category: string]: string[] }>({});
  const [selectedFoods, setSelectedFoods] = useState<{ [category: string]: string[] }>({});
  const [formData, setFormData] = useState({
    age: '',
    weight: '',
    height: '',
    goal: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [ws, setWs] = useState<WebSocket | null>(null);
  const router = useRouter();

  // WebSocket cleanup
  useEffect(() => {
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [ws]);

  const fetchFoods = useCallback(async () => {
    try {
      const res = await fetch('/api/food-db', { credentials: 'include' });
      if (res.status === 401) {
        router.push('/login');
        return;
      }
      if (res.ok) {
        const data = await res.json();
        const grouped = data.reduce((acc: { [key: string]: string[] }, food: { 
          name: string; 
          category: string 
        }) => {
          if (!acc[food.category]) acc[food.category] = [];
          acc[food.category].push(food.name);
          return acc;
        }, {});
        setFoods(grouped);
        setSelectedFoods(
          Object.keys(grouped).reduce((acc, category) => ({
            ...acc,
            [category]: []
          }), {})
        );
      } else {
        setError('Failed to load food options.');
      }
    } catch (err) {
      setError('Error fetching food options');
    }
  }, [router]);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setProgress(0);
    setStatusMessage('Initializing...');

    const newWs = new WebSocket(`wss://${window.location.host}/api/generate-plan-ws`);
    
    newWs.onopen = () => {
      // Send authentication
      const authData = {
        username: localStorage.getItem('username'), // Adjust based on your auth storage
        token: localStorage.getItem('token')
      };
      newWs.send(JSON.stringify(authData));
    };

    newWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'progress':
          setProgress(data.progress * 100);
          setStatusMessage(data.message);
          break;
        case 'complete':
          router.push(`/plan/${data.id}`);
          newWs.close();
          break;
        case 'error':
          setError(data.message);
          setLoading(false);
          newWs.close();
          break;
      }
    };

    newWs.onerror = (error) => {
      setError('Connection error');
      setLoading(false);
    };

    newWs.onclose = () => {
      setLoading(false);
      setWs(null);
    };

    // Wait for authentication confirmation
    const authListener = (event: MessageEvent) => {
      const authResponse = JSON.parse(event.data);
      if (authResponse.error) {
        setError(authResponse.error);
        newWs.close();
        return;
      }
      
      // Send parameters after successful auth
      newWs.send(JSON.stringify({
        ...formData,
        food_preferences: selectedFoods
      }));
      
      // Remove the temporary auth listener
      newWs.removeEventListener('message', authListener);
    };

    newWs.addEventListener('message', authListener);
    setWs(newWs);
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
            <div key={category}> {/* Added a parent wrapper */}
              <h3 className="text-lg font-medium text-gray-700 mb-4 capitalize">{category}</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {items.map((food) => (
                  <label 
                    key={food} 
                    className="flex items-center p-3 space-x-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedFoods[category]?.includes(food) || false}
                      onChange={() => handleFoodToggle(category, food)}
                      className="h-5 w-5 text-green-600 rounded focus:ring-green-500"
                    />
                    <span className="text-gray-700">{food}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </Card>


        <div className="space-y-4">
          {loading && (
            <div className="space-y-2">
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-green-500 transition-all duration-300 ease-out" 
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-sm text-gray-600 text-center">{statusMessage}</p>
            </div>
          )}

            <Button 
              type="submit"
              disabled={loading}
              className="w-full py-4 text-lg font-semibold"
            >
              {loading ? (
                <div className="flex items-center justify-center gap-2">
                  <Loader/>
                  Generating...
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