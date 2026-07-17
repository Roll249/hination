'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { authApi, adminApi } from '@/lib/api';
import toast from 'react-hot-toast';
import Cookies from 'js-cookie';

interface Stats {
  users: number;
  activeSessions: number;
  totalJobs: number;
  jobsLast24h: Record<string, number>;
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, setUser, setLoading, logout } = useAuthStore();
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    // Check authentication
    const checkAuth = async () => {
      const token = localStorage.getItem('accessToken');
      const refreshToken = Cookies.get('refreshToken');
      
      if (!token && !refreshToken) {
        router.push('/login');
        return;
      }

      setLoading(true);

      try {
        if (token) {
          const { user: userData } = await authApi.getMe();
          setUser(userData);
        } else if (refreshToken) {
          const { accessToken, user: userData } = await authApi.refresh(refreshToken);
          localStorage.setItem('accessToken', accessToken);
          setUser(userData);
        }
      } catch (error) {
        // Try refresh token
        try {
          const { accessToken, user: userData } = await authApi.refresh(refreshToken!);
          localStorage.setItem('accessToken', accessToken);
          setUser(userData);
        } catch {
          logout();
          router.push('/login');
          return;
        }
      }
    };

    checkAuth();
  }, [router, setLoading, setUser, logout]);

  useEffect(() => {
    // Fetch stats if authenticated
    if (isAuthenticated) {
      const fetchStats = async () => {
        try {
          const { stats: statsData } = await adminApi.getStats();
          setStats(statsData);
        } catch (error) {
          console.error('Failed to fetch stats:', error);
        }
      };

      fetchStats();
    }
  }, [isAuthenticated]);

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore logout errors
    }
    
    localStorage.removeItem('accessToken');
    Cookies.remove('refreshToken');
    logout();
    toast.success('Logged out successfully');
    router.push('/login');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  const statCards = [
    {
      label: 'Total Jobs',
      value: stats?.totalJobs ?? '-',
      icon: '📋',
      color: 'from-blue-500 to-blue-600',
    },
    {
      label: 'Jobs (24h)',
      value: Object.values(stats?.jobsLast24h ?? {}).reduce((a, b) => a + b, 0),
      icon: '⏱️',
      color: 'from-purple-500 to-purple-600',
    },
    {
      label: 'Active Sessions',
      value: stats?.activeSessions ?? '-',
      icon: '🔐',
      color: 'from-green-500 to-green-600',
    },
    {
      label: 'Users',
      value: stats?.users ?? '-',
      icon: '👥',
      color: 'from-orange-500 to-orange-600',
    },
  ];

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800/50 backdrop-blur-xl border-b border-slate-700/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <span className="text-white text-xl">⚡</span>
              </div>
              <span className="text-xl font-bold text-white">Hination</span>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm font-medium text-white">{user.username}</p>
                <p className="text-xs text-slate-400">{user.role}</p>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-sm transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 mt-1">Overview of the grading system</p>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statCards.map((card) => (
            <div
              key={card.label}
              className="relative overflow-hidden rounded-2xl bg-slate-800/50 border border-slate-700/50 p-6"
            >
              <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${card.color} opacity-10 rounded-full blur-2xl`} />
              <div className="relative">
                <span className="text-4xl mb-4 block">{card.icon}</span>
                <p className="text-slate-400 text-sm mb-1">{card.label}</p>
                <p className="text-3xl font-bold text-white">
                  {typeof card.value === 'number' ? card.value.toLocaleString() : card.value}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Quick actions */}
        <div className="rounded-2xl bg-slate-800/50 border border-slate-700/50 p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => router.push('/scoring')}
              className="flex items-center gap-3 p-4 bg-slate-700/50 hover:bg-slate-700 rounded-xl transition-colors"
            >
              <span className="text-2xl">📊</span>
              <div className="text-left">
                <p className="font-medium text-white">View Jobs</p>
                <p className="text-sm text-slate-400">Check scoring queue</p>
              </div>
            </button>

            <button
              onClick={() => router.push('/settings')}
              className="flex items-center gap-3 p-4 bg-slate-700/50 hover:bg-slate-700 rounded-xl transition-colors"
            >
              <span className="text-2xl">⚙️</span>
              <div className="text-left">
                <p className="font-medium text-white">Settings</p>
                <p className="text-sm text-slate-400">Configure system</p>
              </div>
            </button>

            <button
              onClick={() => window.open('http://localhost:8080/rabbitmq/', '_blank')}
              className="flex items-center gap-3 p-4 bg-slate-700/50 hover:bg-slate-700 rounded-xl transition-colors"
            >
              <span className="text-2xl">🐰</span>
              <div className="text-left">
                <p className="font-medium text-white">RabbitMQ</p>
                <p className="text-sm text-slate-400">Queue management</p>
              </div>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
