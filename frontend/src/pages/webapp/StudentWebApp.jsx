import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts'
import {
  Trophy, Award, Compass, RefreshCw, AlertCircle, Calendar, Zap, LayoutDashboard, History
} from 'lucide-react'

const API_BASE_URL = '/api/webapp'

export default function StudentWebApp() {
  const [tgUserId, setTgUserId] = useState(() => {
    const tgUser = window.Telegram?.WebApp?.initDataUnsafe?.user
    if (tgUser?.id) return tgUser.id
    return localStorage.getItem('dev_student_tg_id') || '123456'
  })

  const [devMode, setDevMode] = useState(!window.Telegram?.WebApp?.initDataUnsafe?.user?.id)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Tabs
  const [activeTab, setActiveTab] = useState('dashboard') // dashboard, leaderboard, history
  const [leaderboardTab, setLeaderboardTab] = useState('weekly')

  const fetchStats = async (userId) => {
    setLoading(true)
    setError('')
    try {
      const res = await axios.get(`${API_BASE_URL}/student/stats`, {
        headers: { 'X-TG-Init-Data': window.Telegram?.WebApp?.initData || `DEV_${userId}` },
        params: { t: Date.now() }
      })
      setStats(res.data)
      if (devMode) {
        localStorage.setItem('dev_student_tg_id', userId)
      }
    } catch (err) {
      console.error(err)
      setError(err.response?.data?.detail || 'Natijalar yuklashda xatolik.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (tgUserId) fetchStats(tgUserId)
  }, [tgUserId])

  const getDifficultyColor = (diff) => {
    switch (diff?.toLowerCase()) {
      case 'easy': return '#22C55E'
      case 'medium': return '#F59E0B'
      case 'hard': return '#EF4444'
      default: return 'var(--primary)'
    }
  }

  if (!stats) {
    if (loading) {
      return (
        <div className="glass-bg" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
          <div className="spinner spinner-primary" style={{ width: '36px', height: '36px', borderWidth: '3px' }} />
          <p style={{ marginTop: '12px', color: 'var(--text-secondary)', fontSize: '14px', fontWeight: '500' }}>Yuklanmoqda...</p>
        </div>
      )
    }
    return null
  }

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
    )
  }

  return (
    <div className="glass-bg-container" style={{ minHeight: '100vh', fontFamily: "'Inter', sans-serif", paddingBottom: '90px', position: 'relative', overflow: 'hidden' }}>

      <div style={{ position: 'relative', zIndex: 1 }}>
        {/* Top Header with Refresh */}
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

          {/* --- TAB: DASHBOARD --- */}
          {activeTab === 'dashboard' && (
            <div className="animate-soft-slide">
              <div className="glass-card premium-hero-card" style={{ padding: '24px 20px', color: '#fff', marginBottom: '24px', position: 'relative', overflow: 'hidden' }}>
                <div style={{ position: 'absolute', top: '-40px', right: '-40px', width: '150px', height: '150px', background: 'rgba(255,255,255,0.2)', borderRadius: '50%', filter: 'blur(10px)' }} />
                <h2 style={{ fontSize: '24px', fontWeight: '800', color: '#fff', display: 'flex', alignItems: 'center', gap: '10px', textShadow: '0 2px 10px rgba(0,0,0,0.2)' }}>
                  <span>{stats.student_name}</span>
                </h2>
                <p style={{ opacity: 0.8, fontSize: '13px', marginTop: '4px' }}>Reyting va o'zlashtirish</p>
                <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                  <div style={{ flex: '1', background: 'rgba(255, 255, 255, 0.15)', borderRadius: '12px', padding: '10px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <span style={{ fontSize: '10px', textTransform: 'uppercase', opacity: 0.8 }}>Haftalik Reyting</span>
                    <span style={{ fontSize: '16px', fontWeight: '800', marginTop: '2px' }}>{stats.weekly_rank ? `#${stats.weekly_rank}` : '—'}</span>
                  </div>
                  <div style={{ flex: '1', background: 'rgba(255, 255, 255, 0.15)', borderRadius: '12px', padding: '10px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <span style={{ fontSize: '10px', textTransform: 'uppercase', opacity: 0.8 }}>Oylik Reyting</span>
                    <span style={{ fontSize: '16px', fontWeight: '800', marginTop: '2px' }}>{stats.monthly_rank ? `#${stats.monthly_rank}` : '—'}</span>
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '24px' }}>
                <div className="glass-card" style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <Zap size={22} style={{ color: 'var(--accent)', marginBottom: '8px' }} />
                  <span style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats.total_xp}</span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600', letterSpacing: '0.5px' }}>XP</span>
                </div>
                <div className="glass-card" style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <Compass size={22} style={{ color: 'var(--primary)', marginBottom: '8px' }} />
                  <span style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats.attempts_count}</span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600', letterSpacing: '0.5px' }}>Yechilgan</span>
                </div>
                <div className="glass-card" style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <Award size={22} style={{ color: 'var(--success)', marginBottom: '8px' }} />
                  <span style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats.average_score}%</span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600', letterSpacing: '0.5px' }}>O'rtacha</span>
                </div>
              </div>

              {stats.progress_trends && stats.progress_trends.length > 0 && (
                <div className="glass-card" style={{ padding: '20px', marginBottom: '24px' }}>
                  <h3 style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Zap size={16} className="text-primary" /><span>Mening XP O'sish Grafikim</span>
                  </h3>
                  <div style={{ width: '100%', height: '180px' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={stats.progress_trends}>
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
          )}

          {/* --- TAB: LEADERBOARD --- */}
          {activeTab === 'leaderboard' && (
            <div className="animate-soft-slide glass-card" style={{ padding: '24px 20px', marginBottom: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Trophy size={18} style={{ color: 'var(--accent)' }} /><span>Etakchilar Reytingi</span>
              </h3>

              <div style={{ display: 'flex', background: 'rgba(0,0,0,0.25)', borderRadius: '12px', padding: '4px', marginBottom: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
                <button
                  onClick={() => setLeaderboardTab('weekly')}
                  style={{ flex: 1, padding: '10px', borderRadius: '10px', background: leaderboardTab === 'weekly' ? 'var(--primary)' : 'transparent', color: leaderboardTab === 'weekly' ? '#1a1a2e' : '#fff', fontWeight: '700', transition: 'all 0.2s', border: 'none' }}
                >
                  Haftalik
                </button>
                <button
                  onClick={() => setLeaderboardTab('monthly')}
                  style={{ flex: 1, padding: '10px', borderRadius: '10px', background: leaderboardTab === 'monthly' ? 'var(--primary)' : 'transparent', color: leaderboardTab === 'monthly' ? '#1a1a2e' : '#fff', fontWeight: '700', transition: 'all 0.2s', border: 'none' }}
                >
                  Oylik
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {(leaderboardTab === 'weekly' ? (stats.weekly_leaderboard || []) : (stats.monthly_leaderboard || [])).length === 0 ? (
                  <p style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', padding: '10px 0' }}>Reyting mavjud emas</p>
                ) : (
                  (leaderboardTab === 'weekly' ? (stats.weekly_leaderboard || []) : (stats.monthly_leaderboard || [])).map((row) => (
                    <div key={row.rank} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: row.student_name === stats.student_name ? 'var(--bg-card-hover)' : 'transparent', borderRadius: '8px', border: row.student_name === stats.student_name ? '1px solid var(--primary-light)' : 'none', fontSize: '13px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ width: '24px', height: '24px', borderRadius: '50%', background: row.rank === 1 ? '#FEF08A' : row.rank === 2 ? '#E5E7EB' : row.rank === 3 ? '#FED7AA' : 'transparent', color: row.rank <= 3 ? '#92400E' : 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '800', fontSize: '12px' }}>{row.rank}</span>
                        <span style={{ fontWeight: row.student_name === stats.student_name ? '700' : '600', color: 'var(--text-primary)' }}>{row.student_name}</span>
                      </div>
                      <strong style={{ color: 'var(--primary)' }}>{row.xp} XP</strong>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* --- TAB: HISTORY --- */}
          {activeTab === 'history' && (
            <div className="animate-soft-slide">
              <h2 style={{ fontSize: '20px', fontWeight: '800', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Calendar size={20} className="text-primary" /> Yechilgan Testlar Tarixi
              </h2>

              {(!stats.attempts || stats.attempts.length === 0) ? (
                <p style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', padding: '20px 0' }}>Hozircha testlar yechilmagan.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {stats.attempts.map((att, i) => (
                    <div key={i} className="glass-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <h4 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text-primary)', flex: '1', paddingRight: '8px' }}>{att.test_title}</h4>
                        <span className="badge" style={{ background: 'rgba(165, 180, 252, 0.15)', color: 'var(--primary)', fontFamily: 'monospace', fontSize: '11px' }}>{att.test_code}</span>
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center', fontSize: '12px' }}>
                        <span style={{ background: getDifficultyColor(att.difficulty) + '15', color: getDifficultyColor(att.difficulty), padding: '2px 8px', borderRadius: '12px', fontWeight: 'bold' }}>{(att.difficulty || '').toUpperCase()}</span>
                        <span style={{ color: 'var(--text-muted)' }}>📅 {att.date}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--divider)', paddingTop: '8px', fontSize: '12px', fontWeight: '500' }}>
                        <span>To'g'ri javoblar: <strong style={{ color: 'var(--text-primary)' }}>{att.score} / {att.max_score} ({att.percent || 0}%)</strong></span>
                        <span style={{ color: 'var(--success)', fontWeight: 'bold' }}>+{att.xp_earned} XP</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* --- BOTTOM NAVIGATION --- */}
        <div className="glass-nav" style={{
          position: 'fixed', bottom: '16px', left: '16px', right: '16px',
          borderRadius: '15px', display: 'flex', justifyContent: 'space-around',
          padding: '12px 8px', zIndex: 50
        }}>
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            style={{ background: 'none', border: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', cursor: 'pointer', flex: 1 }}
          >
            <div className="nav-icon-bg" style={{ padding: '8px 20px', borderRadius: '16px' }}>
              <LayoutDashboard size={22} strokeWidth={activeTab === 'dashboard' ? 2.5 : 2} />
            </div>
            <span style={{ fontSize: '11px', fontWeight: activeTab === 'dashboard' ? '700' : '600' }}>Asosiy</span>
          </button>
          <button
            onClick={() => setActiveTab('leaderboard')}
            className={`nav-item ${activeTab === 'leaderboard' ? 'active' : ''}`}
            style={{ background: 'none', border: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', cursor: 'pointer', flex: 1 }}
          >
            <div className="nav-icon-bg" style={{ padding: '8px 20px', borderRadius: '16px' }}>
              <Trophy size={22} strokeWidth={activeTab === 'leaderboard' ? 2.5 : 2} />
            </div>
            <span style={{ fontSize: '11px', fontWeight: activeTab === 'leaderboard' ? '700' : '600' }}>Reyting</span>
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`nav-item ${activeTab === 'history' ? 'active' : ''}`}
            style={{ background: 'none', border: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', cursor: 'pointer', flex: 1 }}
          >
            <div className="nav-icon-bg" style={{ padding: '8px 20px', borderRadius: '16px' }}>
              <History size={22} strokeWidth={activeTab === 'history' ? 2.5 : 2} />
            </div>
            <span style={{ fontSize: '11px', fontWeight: activeTab === 'history' ? '700' : '600' }}>Tarix</span>
          </button>
        </div>
      </div>
    </div>
  )
}
