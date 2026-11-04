import { useState, useEffect } from 'react';
import { analyticsAPI } from '../api';
import { Users, UserCheck, BookOpen, ClipboardCheck, Clock, TrendingUp } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './Dashboard.css';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [userGrowth, setUserGrowth] = useState([]);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, growthRes, activityRes] = await Promise.all([
        analyticsAPI.dashboard(),
        analyticsAPI.userGrowth(30),
        analyticsAPI.activity(30),
      ]);
      setStats(statsRes.data);
      setUserGrowth(growthRes.data);
      setActivity(activityRes.data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading-screen"><div className="loading-spinner"></div></div>;
  }

  const statCards = [
    { icon: Users, label: 'Foydalanuvchilar', value: stats?.total_users || 0, color: 'var(--accent)', bg: 'rgba(10, 132, 255, 0.12)' },
    { icon: UserCheck, label: "O'qituvchilar", value: stats?.total_teachers || 0, color: 'var(--purple)', bg: 'rgba(191, 90, 242, 0.12)' },
    { icon: BookOpen, label: 'Testlar', value: stats?.total_tests || 0, color: 'var(--success)', bg: 'rgba(48, 209, 88, 0.12)' },
    { icon: ClipboardCheck, label: 'Urinishlar', value: stats?.total_attempts || 0, color: 'var(--warning)', bg: 'rgba(255, 214, 10, 0.12)' },
    { icon: Clock, label: "So'rovlar", value: stats?.pending_requests || 0, color: 'var(--danger)', bg: 'rgba(255, 69, 58, 0.12)' },
  ];

  const tooltipStyle = {
    background: 'rgba(20, 20, 30, 0.85)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '10px',
    fontSize: '12px',
    color: '#fff',
    padding: '8px 12px',
  };

  return (
    <div className="dashboard">
      <h1 className="page-title">Dashboard</h1>

      <div className="stats-grid">
        {statCards.map((card, i) => (
          <div key={i} className="stat-card glass-card">
            <div className="stat-icon" style={{ background: card.bg, color: card.color }}>
              <card.icon size={20} />
            </div>
            <div className="stat-info">
              <span className="stat-value">{card.value}</span>
              <span className="stat-label">{card.label}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="charts-grid">
        <div className="chart-card glass-card">
          <div className="chart-header">
            <TrendingUp size={16} style={{ color: 'var(--accent)' }} />
            <h3>Foydalanuvchilar o'sishi</h3>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={userGrowth}>
              <defs>
                <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" stroke="rgba(255,255,255,0.25)" fontSize={10} tickLine={false} axisLine={false} />
              <YAxis stroke="rgba(255,255,255,0.25)" fontSize={10} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Line type="monotone" dataKey="count" stroke="var(--accent)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card glass-card">
          <div className="chart-header">
            <ClipboardCheck size={16} style={{ color: 'var(--purple)' }} />
            <h3>Test faolligi</h3>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={activity}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" stroke="rgba(255,255,255,0.25)" fontSize={10} tickLine={false} axisLine={false} />
              <YAxis stroke="rgba(255,255,255,0.25)" fontSize={10} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="count" fill="var(--purple)" radius={[6, 6, 0, 0]} opacity={0.8} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
