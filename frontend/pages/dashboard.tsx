// pages/dashboard.tsx
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';

export default function Dashboard() {
  const [plans, setPlans] = useState<{ id: string; date: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const res = await fetch('/api/meal-plans', { credentials: 'include' });
        if (res.status === 401) {
          router.push('/login');
          return;
        }
        if (res.ok) {
          const data = await res.json();
          setPlans(data);
        } else {
          setError('Failed to fetch meal plans.');
        }
      } catch (err) {
        setError('An error occurred. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchPlans();
  }, [router]);

  if (loading) {
    return <div className="text-center mt-10">Loading...</div>;
  }

  if (error) {
    return <div className="text-center mt-10 text-red-500">{error}</div>;
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Your Meal Plans</h1>
      {plans.length === 0 ? (
        <p className="text-gray-600">No meal plans yet. Create one now!</p>
      ) : (
        <ul className="space-y-2">
          {plans.map((plan) => (
            <li key={plan.id}>
              <Link
                className="text-blue-500 hover:underline"
                href={`/plan/${plan.id}`}
                legacyBehavior>
               {plan.date}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}