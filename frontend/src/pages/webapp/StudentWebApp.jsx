import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import axios from 'axios';
import { useTelegram } from '../../hooks/useTelegram';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts';
import {
  Trophy, Award, Compass, RefreshCw, AlertCircle, Calendar, Zap, LayoutDashboard, History
} from 'lucide-react';

const API_BASE_URL = '/api/webapp';

// --- Utility Functions ---
const getDifficultyColor = (diff) => {
  const safeDiff = String(diff || '').toLowerCase();
  switch (safeDiff) {
    case 'easy': return '#22C55E';
    case 'medium': return '#F59E0B';
    case 'hard': return '#EF4444';
    default: return 'var(--primary)';
  }
};

// --- Sub-Components ---
// 1. Dashboard Tab
const DashboardTab = React.memo(({ stats }) => {
  const safeTrends = useMemo(() => {
    return Array.isArray(stats?.progress_trends) 
      ? stats.progress_trends.filter(item => item && typeof item === 'object') 
      : [];
  }, [stats?.progress_trends]);

  return (
    <div className="animate-soft-slide">
      <div className="glass-card premium-hero-card" style={{ padding: '24px 20px', color: '#fff', marginBottom: '24px', position: 'relative', overflow: 'hidden' }}>
        <h2 style={{ fontSize: '24px', fontWeight: '800', color: '#fff', display: 'flex', alignItems: 'center', gap: '10px', textShadow: '0 2px 10px rgba(0,0,0,0.2)' }}>
          <span>{stats?.student_name || 'Noma\'lum o\'quvchi'}</span>
        </h2>
        <p style={{ opacity: 0.8, fontSize: '13px', marginTop: '4px' }}>Reyting va o'zlashtirish</p>
        <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
          <div style={{ flex: '1', background: 'rgba(255, 255, 255, 0.15)', borderRadius: '12px', padding: '10px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ fontSize: '10px', textTransform: 'uppercase', opacity: 0.8 }}>Haftalik Reyting</span>
            <span style={{ fontSize: '16px', fontWeight: '800', marginTop: '2px' }}>{stats?.weekly_rank ? `#${stats.weekly_rank}` : '—'}</span>
          </div>
          <div style={{ flex: '1', background: 'rgba(255, 255, 255, 0.15)', borderRadius: '12px', padding: '10px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ fontSize: '10px', textTransform: 'uppercase', opacity: 0.8 }}>Oylik Reyting</span>
            <span style={{ fontSize: '16px', fontWeight: '800', marginTop: '2px' }}>{stats?.monthly_rank ? `#${stats.monthly_rank}` : '—'}</span>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '24px' }}>
        <div className="glass-card" style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Zap size={22} style={{ color: 'var(--accent)', marginBottom: '8px' }} />
          <span style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats?.total_xp || 0}</span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600', letterSpacing: '0.5px' }}>XP</span>
        </div>
        <div className="glass-card" style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Compass size={22} style={{ color: 'var(--primary)', marginBottom: '8px' }} />
          <span style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats?.attempts_count || 0}</span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600', letterSpacing: '0.5px' }}>Yechilgan</span>
        </div>
        <div className="glass-card" style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Award size={22} style={{ color: 'var(--success)', marginBottom: '8px' }} />
          <span style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats?.average_score || 0}%</span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600', letterSpacing: '0.5px' }}>O'rtacha</span>
        </div>
      </div>

      {safeTrends.length > 0 && (
        <div className="glass-card" style={{ padding: '20px', marginBottom: '24px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Zap size={16} className="text-primary" /><span>Mening XP O'sish Grafikim</span>
          </h3>
          <div style={{ width: '100%', height: '180px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={safeTrends}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.15)" />
                <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: '10px' }} />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: '10px' }} />
                <Tooltip labelStyle={{ fontSize: '11px' }} itemStyle={{ fontSize: '11px' }} />
                <Line type="monotone" dataKey="cumulative_xp" stroke="var(--primary)" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
});

// 2. Leaderboard Tab
const LeaderboardTab = React.memo(({ stats }) => {
  const [leaderboardTab, setLeaderboardTab] = useState('weekly');

  const currentLeaderboard = useMemo(() => {
    const board = leaderboardTab === 'weekly' ? stats?.weekly_leaderboard : stats?.monthly_leaderboard;
    return Array.isArray(board) ? board : [];
  }, [leaderboardTab, stats]);

  return (
    <div className="animate-soft-slide glass-card" style={{ padding: '24px 20px', marginBottom: '24px' }}>
      <h3 style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Trophy size={18} style={{ color: 'var(--accent)' }} /><span>Etakchilar Reytingi</span>
      </h3>

      <div className="glass-tab-container" style={{ marginBottom: '20px' }}>
        <button
          onClick={() => setLeaderboardTab('weekly')}
          className={`glass-tab-btn ${leaderboardTab === 'weekly' ? 'active' : ''}`}
        >
          Haftalik
        </button>
        <button
          onClick={() => setLeaderboardTab('monthly')}
          className={`glass-tab-btn ${leaderboardTab === 'monthly' ? 'active' : ''}`}
        >
          Oylik
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {currentLeaderboard.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', padding: '10px 0' }}>Reyting mavjud emas</p>
        ) : (
          currentLeaderboard.map((row, index) => {
            const isMe = row?.student_name === stats?.student_name;
            const rank = row?.rank || index + 1;
            return (
              <div key={row?.id || `rank-${index}`} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: isMe ? 'var(--bg-card-hover)' : 'transparent', borderRadius: '8px', border: isMe ? '1px solid var(--primary-light)' : 'none', fontSize: '13px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ width: '24px', height: '24px', borderRadius: '50%', background: rank === 1 ? '#FEF08A' : rank === 2 ? '#E5E7EB' : rank === 3 ? '#FED7AA' : 'transparent', color: rank <= 3 ? '#92400E' : 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '800', fontSize: '12px' }}>{rank}</span>
                  <span style={{ fontWeight: isMe ? '700' : '600', color: 'var(--text-primary)' }}>{row?.student_name || 'Noma\'lum'}</span>
                </div>
                <strong style={{ color: 'var(--primary)' }}>{row?.xp || 0} XP</strong>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
});

// 3. History Tab
const HistoryTab = React.memo(({ stats }) => {
  const safeAttempts = useMemo(() => {
    return Array.isArray(stats?.attempts) ? stats.attempts : [];
  }, [stats?.attempts]);

  // Optimizatsiya: DOM qotib qolmasligi uchun faqat oxirgi 50 ta element ko'rsatiladi
  const displayedAttempts = safeAttempts.slice(0, 50);

  return (
    <div className="animate-soft-slide">
      <h2 style={{ fontSize: '20px', fontWeight: '800', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Calendar size={20} className="text-primary" /> Yechilgan Testlar Tarixi
      </h2>

      {displayedAttempts.length === 0 ? (
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', padding: '20px 0' }}>Hozircha testlar yechilmagan yoki ma'lumot yo'q.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {displayedAttempts.map((att, index) => {
             const key = att?.id || att?.attempt_id || `att-${index}`;
             const difficultyStr = String(att?.difficulty || '').toUpperCase();
             return (
              <div key={key} className="glass-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text-primary)', flex: '1', paddingRight: '8px' }}>{att?.test_title || 'Nomsiz test'}</h4>
                  <span className="badge" style={{ background: '#1e293b', color: 'var(--primary-light)', border: '1px solid #334155', fontFamily: 'monospace', fontSize: '11px' }}>{att?.test_code || '---'}</span>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center', fontSize: '12px' }}>
                  {difficultyStr && (
                    <span style={{ background: '#1e293b', color: getDifficultyColor(difficultyStr), border: '1.5px solid ' + getDifficultyColor(difficultyStr), padding: '2px 8px', borderRadius: '12px', fontWeight: 'bold' }}>{difficultyStr}</span>
                  )}
                  {att?.status === 'expired' && (
                    <span style={{ background: '#1e293b', color: '#ef4444', border: '1.5px solid #ef4444', padding: '2px 8px', borderRadius: '12px', fontWeight: '800' }}>MUDDATI O'TGAN</span>
                  )}
                  <span style={{ color: 'var(--text-muted)' }}>📅 {att?.date || 'Sana yo\'q'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--divider)', paddingTop: '8px', fontSize: '12px', fontWeight: '500', alignItems: 'center' }}>
                  <span>To'g'ri javoblar: <strong style={{ color: 'var(--text-primary)' }}>{att?.score || 0} / {att?.max_score || 0} ({att?.percent || 0}%)</strong></span>
                  <span className="badge-percent badge-percent-success">
                    +{att?.xp_earned || 0} XP
                  </span>
                </div>
              </div>
            );
          })}
          {safeAttempts.length > 50 && (
             <p style={{ color: 'var(--text-muted)', fontSize: '12px', textAlign: 'center', marginTop: '10px' }}>Faqat oxirgi 50 ta natija ko'rsatilmoqda.</p>
          )}
        </div>
      )}
    </div>
  );
});

// --- Main Application Component ---
export default function StudentWebApp() {
  const { tg, user, initData } = useTelegram();

  const [tgUserId, setTgUserId] = useState(() => {
    // DEV check
    if (import.meta.env.DEV) {
       return localStorage.getItem('dev_student_tg_id') || '8935558785';
    }
    return '';
  });

  // Sync user ID once Telegram is ready
  useEffect(() => {
    if (user?.id) setTgUserId(String(user.id));
  }, [user]);

  const [devMode, setDevMode] = useState(import.meta.env.DEV);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Tabs
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // AbortController for manual refreshes
  const abortControllerRef = useRef(null);

  const fetchStats = useCallback(async (userId, signal) => {
    if (!userId) {
       setError("Foydalanuvchi IDsi topilmadi. Iltimos, Telegram orqali kiring.");
       setLoading(false);
       return;
    }

    // Abort any ongoing request if this is a manual fetch (no external signal passed)
    if (!signal) {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();
      signal = abortControllerRef.current.signal;
    }

    setLoading(true);
    setError('');
    
    try {
      // XAVFSIZLIK: Productionda hech qachon DEV token jo'natilmaydi
      const actualInitData = initData || (import.meta.env.DEV ? `DEV_${userId}` : '');
      
      const res = await axios.get(`${API_BASE_URL}/student/stats`, {
        headers: { 'X-TG-Init-Data': actualInitData },
        params: { t: Date.now() },
        signal: signal // Race Condition ni oldini olish uchun
      });
      
      setStats(res.data);
      
      if (import.meta.env.DEV) {
        localStorage.setItem('dev_student_tg_id', userId);
      }
    } catch (err) {
      if (axios.isCancel(err)) return; // Bekor qilingan so'rovlarni e'tiborsiz qoldirish
      console.error('Fetch Stats Error:', err);
      setError(err.response?.data?.detail || "Natijalar yuklashda xatolik yuz berdi. Iltimos qayta urinib ko'ring.");
    } finally {
      setLoading(false);
    }
  }, [initData]);

  useEffect(() => {
    // Wait for initData in production before fetching
    if (!initData && !import.meta.env.DEV) return;
    
    // AbortController yordamida Race Condition ni to'xtatish
    const controller = new AbortController();
    fetchStats(tgUserId, controller.signal);
    
    return () => {
      controller.abort();
    };
  }, [tgUserId, fetchStats, initData]);

  if (error) {
    return (
      <div className="glass-bg" style={{ padding: '20px', minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <div className="glass-card" style={{ padding: '32px 24px', textAlign: 'center' }}>
          <AlertCircle size={48} style={{ color: 'var(--error)', marginBottom: '16px', marginInline: 'auto' }} />
          <h3 style={{ color: 'var(--text-primary)', marginBottom: '8px', fontSize: '20px', fontWeight: '800' }}>Xatolik</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '24px' }}>{error}</p>
          <button className="btn btn-primary" onClick={() => fetchStats(tgUserId)}>Qayta urinish</button>
        </div>
      </div>
    );
  }

  if (!stats) {
    if (loading) {
      return (
        <div className="glass-bg" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
          <div className="spinner spinner-primary" style={{ width: '36px', height: '36px', borderWidth: '3px' }} />
          <p style={{ marginTop: '12px', color: 'var(--text-secondary)', fontSize: '14px', fontWeight: '500' }}>Yuklanmoqda...</p>
        </div>
      );
    }
    return null;
  }

  return (
    <div className="glass-bg-container" style={{ minHeight: '100vh', fontFamily: "'Inter', sans-serif", paddingBottom: '90px', position: 'relative', overflow: 'hidden' }}>

      <div style={{ position: 'relative', zIndex: 1 }}>
        <div className="glass-nav" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'sticky', top: 0, zIndex: 10 }}>
          <h1 style={{ fontSize: '18px', fontWeight: '800', color: 'var(--primary)', margin: 0 }}>O'quvchi</h1>
          <button onClick={() => fetchStats(tgUserId)} disabled={loading} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <RefreshCw size={20} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          </button>
        </div>

        <div style={{ padding: '16px' }}>
          {devMode && (
            <div style={{ background: 'rgba(255, 255, 255, 0.05)', border: '1px dashed var(--primary)', borderRadius: '12px', padding: '12px', marginBottom: '16px' }}>
              <p style={{ fontSize: '12px', fontWeight: 'bold', color: 'var(--primary)', marginBottom: '8px' }}>🛠️ Dev Mode</p>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input type="text" className="form-input" value={tgUserId} onChange={(e) => setTgUserId(e.target.value)} style={{ padding: '6px 12px', fontSize: '13px', flex: '1' }} />
                <button className="btn btn-primary btn-sm" onClick={() => fetchStats(tgUserId)}><RefreshCw size={12} /></button>
              </div>
            </div>
          )}

          <div style={{ display: activeTab === 'dashboard' ? 'block' : 'none' }}>
            <DashboardTab stats={stats} />
          </div>
          <div style={{ display: activeTab === 'leaderboard' ? 'block' : 'none' }}>
            <LeaderboardTab stats={stats} />
          </div>
          <div style={{ display: activeTab === 'history' ? 'block' : 'none' }}>
            <HistoryTab stats={stats} />
          </div>
        </div>

        {/* --- BOTTOM NAVIGATION --- */}
        <div className="glass-nav" style={{
          position: 'fixed', bottom: '16px', left: '16px', right: '16px',
          borderRadius: '30px', display: 'flex', justifyContent: 'space-around',
          padding: '12px 8px', zIndex: 50
        }}>
          {[
            { id: 'dashboard', icon: LayoutDashboard, label: 'Asosiy' },
            { id: 'leaderboard', icon: Trophy, label: 'Reyting' },
            { id: 'history', icon: History, label: 'Tarix' }
          ].map((nav) => (
            <button
              key={nav.id}
              onClick={() => setActiveTab(nav.id)}
              className={`nav-item ${activeTab === nav.id ? 'active' : ''}`}
              style={{ background: 'none', border: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', cursor: 'pointer', flex: 1 }}
            >
              <div className="nav-icon-bg" style={{ padding: '8px 20px', borderRadius: '16px' }}>
                <nav.icon size={22} strokeWidth={activeTab === nav.id ? 2.5 : 2} />
              </div>
              <span style={{ fontSize: '11px', fontWeight: activeTab === nav.id ? '700' : '600' }}>{nav.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
