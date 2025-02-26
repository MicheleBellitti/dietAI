// components/Layout.tsx
import Link from 'next/link';
import { useRouter } from 'next/router';
import { ReactNode } from 'react';

export default function Layout({ children }: { children: ReactNode }) {
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await fetch('/api/logout', {
        method: 'POST',
        credentials: 'include',
      });
      router.push('/login');
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-gray-800 p-4">
        <ul className="flex space-x-6 text-white max-w-7xl mx-auto">
          <li>
            <Link href="/dashboard" className="hover:text-gray-300">
              Dashboard
            </Link>
          </li>
          <li>
            <Link href="/generate-plan" className="hover:text-gray-300">
              Generate Plan
            </Link>
          </li>
          <li>
            <button onClick={handleLogout} className="hover:text-gray-300">
              Logout
            </button>
          </li>
        </ul>
      </nav>
      <main className="max-w-7xl mx-auto p-4">{children}</main>
    </div>
  );
}