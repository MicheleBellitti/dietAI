// pages/plan/[id].tsx
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import ReactMarkdown from 'react-markdown';

export default function Plan() {
  const [plan, setPlan] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const router = useRouter();
  const { id } = router.query;

  useEffect(() => {
    if (!id) return;

    const fetchPlan = async () => {
      try {
        const res = await fetch(`/api/meal-plans/${id}`, { credentials: 'include' });
        if (res.status === 401) {
          router.push('/login');
          return;
        }
        if (res.ok) {
          const data = await res.json();
          setPlan(data.plan);
        } else {
          setError('Failed to fetch meal plan.');
        }
      } catch (err) {
        setError('An error occurred. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchPlan();
  }, [id, router]);

  if (loading) {
    return <div className="text-center mt-10">Loading...</div>;
  }

  if (error) {
    return <div className="text-center mt-10 text-red-500">{error}</div>;
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Meal Plan</h1>
      <div className="prose max-w-none">
        <ReactMarkdown>{plan}</ReactMarkdown>
      </div>
    </div>
  );
}