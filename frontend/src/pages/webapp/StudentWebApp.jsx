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

  if (loading && !stats) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#F8F9FE' }}>
        <div className="spinner spinner-primary" style={{ width: '36px', height: '36px', borderWidth: '3px' }} />
        <p style={{ marginTop: '12px', color: 'var(--text-muted)', fontSize: '14px' }}>Yuklanmoqda...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '20px', background: '#F8F9FE', minHeight: '100vh' }}>
        <div className="card" style={{ padding: '24px', textAlign: 'center', marginTop: '40px' }}>
          <AlertCircle size={40} style={{ color: 'var(--error)', marginBottom: '12px', marginInline: 'auto' }} />
          <h3 style={{ color: 'var(--text-primary)', marginBottom: '8px' }}>Xatolik</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginBottom: '20px' }}>{error}</p>
          <button className="btn btn-primary" onClick={() => fetchStats(tgUserId)}>Qayta urinish</button>
        </div>
      </div>
    )
  }

  return (
    <div style={{ background: '#F8F9FE', minHeight: '100vh', fontFamily: "'Inter', sans-serif", paddingBottom: '70px' }}>
      
      {/* Top Header with Refresh */}
      <div style={{ background: '#FFF', padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 2px 10px rgba(0,0,0,0.05)', position: 'sticky', top: 0, zIndex: 10 }}>
        <h1 style={{ fontSize: '18px', fontWeight: '800', color: 'var(--primary)', margin: 0 }}>O'quvchi</h1>
        <button onClick={() => fetchStats(tgUserId)} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', padding: '4px' }}>
          <RefreshCw size={20} />
        </button>
      </div>

      <div style={{ padding: '16px' }}>
        {devMode && (
          <div style={{ background: '#EEF0FF', border: '1px dashed var(--primary)', borderRadius: '12px', padding: '12px', marginBottom: '16px' }}>
            <p style={{ fontSize: '12px', fontWeight: 'bold', color: 'var(--primary)', marginBottom: '8px' }}>🛠️ Dev Mode</p>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input type="text" className="form-input" value={tgUserId} onChange={(e) => setTgUserId(e.target.value)} style={{ padding: '6px 12px', fontSize: '13px', flex: '1' }} />
              <button className="btn btn-primary btn-sm" onClick={() => fetchStats(tgUserId)}><RefreshCw size={12}/></button>
            </div>
          </div>
        )}

        {/* --- TAB: DASHBOARD --- */}
        {activeTab === 'dashboard' && (
          <div className="animate-fade">
            <div style={{ background: 'linear-gradient(135deg, #6B7FE8 0%, var(--primary) 100%)', borderRadius: '16px', padding: '24px 20px', color: '#fff', marginBottom: '20px', boxShadow: '0 10px 25px rgba(91, 111, 232, 0.2)', position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: '-10px', right: '-10px', width: '90px', height: '90px', background: 'rgba(255,255,255,0.08)', borderRadius: '50%' }} />
              <h2 style={{ fontSize: '22px', fontWeight: '800', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>O'quvchi:</span><span>{stats.student_name}</span>
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

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '20px' }}>
              <div className="card" style={{ padding: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <Zap size={18} style={{ color: 'var(--accent)', marginBottom: '4px' }} />
                <span style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats.total_xp} XP</span>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Jami tajriba</span>
              </div>
              <div className="card" style={{ padding: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <Compass size={18} style={{ color: 'var(--primary)', marginBottom: '4px' }} />
                <span style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats.attempts_count} marta</span>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Yechilgan</span>
              </div>
              <div className="card" style={{ padding: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <Award size={18} style={{ color: 'var(--success)', marginBottom: '4px' }} />
                <span style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats.average_score}%</span>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>O'rtacha ball</span>
              </div>
            </div>

            {stats.progress_trends && stats.progress_trends.length > 0 && (
              <div className="card" style={{ padding: '20px', marginBottom: '24px' }}>
                <h3 style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Zap size={16} className="text-primary" /><span>Mening XP O'sish Grafikim</span>
                </h3>
                <div style={{ width: '100%', height: '180px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={stats.progress_trends}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
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
          <div className="animate-fade card" style={{ padding: '20px', marginBottom: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Trophy size={18} style={{ color: 'var(--accent)' }} /><span>Etakchilar Reytingi</span>
            </h3>

            <div style={{ display: 'flex', background: '#F3F4F6', borderRadius: '8px', padding: '4px', marginBottom: '16px' }}>
              <button onClick={() => setLeaderboardTab('weekly')} style={{ flex: '1', padding: '8px 12px', borderRadius: '6px', fontSize: '13px', fontWeight: '600', background: leaderboardTab === 'weekly' ? '#fff' : 'transparent', color: leaderboardTab === 'weekly' ? 'var(--primary)' : 'var(--text-secondary)', boxShadow: leaderboardTab === 'weekly' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none', transition: 'all 0.2s', border: 'none' }}>Haftalik</button>
              <button onClick={() => setLeaderboardTab('monthly')} style={{ flex: '1', padding: '8px 12px', borderRadius: '6px', fontSize: '13px', fontWeight: '600', background: leaderboardTab === 'monthly' ? '#fff' : 'transparent', color: leaderboardTab === 'monthly' ? 'var(--primary)' : 'var(--text-secondary)', boxShadow: leaderboardTab === 'monthly' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none', transition: 'all 0.2s', border: 'none' }}>Oylik</button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {(leaderboardTab === 'weekly' ? stats.weekly_leaderboard : stats.monthly_leaderboard).length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', padding: '10px 0' }}>Reyting mavjud emas</p>
              ) : (
                (leaderboardTab === 'weekly' ? stats.weekly_leaderboard : stats.monthly_leaderboard).map((row) => (
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
          <div className="animate-fade">
            <h2 style={{ fontSize: '18px', fontWeight: '800', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Calendar size={20} className="text-primary" /> Yechilgan Testlar Tarixi
            </h2>

            {stats.attempts.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', padding: '20px 0' }}>Hozircha testlar yechilmagan.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {stats.attempts.map((att, i) => (
                  <div key={i} style={{ padding: '12px 14px', background: '#FFF', border: '1.5px solid var(--border)', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <h4 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text-primary)', flex: '1', paddingRight: '8px' }}>{att.test_title}</h4>
                      <span className="badge" style={{ background: '#EEF0FF', color: 'var(--primary)', fontFamily: 'monospace', fontSize: '11px' }}>{att.test_code}</span>
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center', fontSize: '12px' }}>
                      <span style={{ background: getDifficultyColor(att.difficulty) + '15', color: getDifficultyColor(att.difficulty), padding: '2px 8px', borderRadius: '12px', fontWeight: 'bold' }}>{att.difficulty.toUpperCase()}</span>
                      <span style={{ color: 'var(--text-muted)' }}>📅 {att.date}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--divider)', paddingTop: '8px', fontSize: '12px', fontWeight: '500' }}>
                      <span>To'g'ri javoblar: <strong style={{ color: 'var(--text-primary)' }}>{att.score} / {att.max_score} ({att.percent}%)</strong></span>
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
      <div style={{ 
        position: 'fixed', bottom: 0, left: 0, right: 0, background: '#FFF', 
        borderTop: '1px solid var(--divider)', display: 'flex', justifyContent: 'space-around', 
        padding: '10px 0', paddingBottom: 'calc(10px + env(safe-area-inset-bottom))', zIndex: 50,
        boxShadow: '0 -4px 10px rgba(0,0,0,0.02)'
      }}>
        <button 
          onClick={() => setActiveTab('dashboard')} 
          style={{ background: 'none', border: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', cursor: 'pointer', color: activeTab === 'dashboard' ? 'var(--primary)' : 'var(--text-muted)' }}
        >
          <LayoutDashboard size={22} strokeWidth={activeTab === 'dashboard' ? 2.5 : 2} />
          <span style={{ fontSize: '10px', fontWeight: activeTab === 'dashboard' ? '700' : '500' }}>Asosiy</span>
        </button>
        <button 
          onClick={() => setActiveTab('leaderboard')} 
          style={{ background: 'none', border: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', cursor: 'pointer', color: activeTab === 'leaderboard' ? 'var(--primary)' : 'var(--text-muted)' }}
        >
          <Trophy size={22} strokeWidth={activeTab === 'leaderboard' ? 2.5 : 2} />
          <span style={{ fontSize: '10px', fontWeight: activeTab === 'leaderboard' ? '700' : '500' }}>Reyting</span>
        </button>
        <button 
          onClick={() => setActiveTab('history')} 
          style={{ background: 'none', border: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', cursor: 'pointer', color: activeTab === 'history' ? 'var(--primary)' : 'var(--text-muted)' }}
        >
          <History size={22} strokeWidth={activeTab === 'history' ? 2.5 : 2} />
          <span style={{ fontSize: '10px', fontWeight: activeTab === 'history' ? '700' : '500' }}>Tarix</span>
        </button>
      </div>
    </div>
  )
}
