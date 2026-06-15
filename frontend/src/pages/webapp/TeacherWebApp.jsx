import { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid
} from 'recharts'
import { 
  Sparkles, Award, BarChart3, Users, HelpCircle, 
  ChevronRight, CheckCircle, AlertCircle, RefreshCw, Layers, LayoutDashboard, Wand2, X, Edit2
} from 'lucide-react'

const API_BASE_URL = '/api/webapp'

export default function TeacherWebApp() {
  const [tgUserId, setTgUserId] = useState(() => {
    const tgUser = window.Telegram?.WebApp?.initDataUnsafe?.user
    if (tgUser?.id) return tgUser.id
    return localStorage.getItem('dev_teacher_tg_id') || '789123'
  })
  
  const initData = window.Telegram?.WebApp?.initData || `DEV_${tgUserId}`
  
  const [devMode, setDevMode] = useState(!window.Telegram?.WebApp?.initDataUnsafe?.user?.id)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  // Tabs
  const [activeTab, setActiveTab] = useState('dashboard')
  const [statusFilter, setStatusFilter] = useState('Barchasi')

  // Test Details Modal
  const [selectedTestId, setSelectedTestId] = useState(null)
  const [testDetails, setTestDetails] = useState(null)
  const [loadingDetails, setLoadingDetails] = useState(false)
  
  // AI Generator Form States
  const [topic, setTopic] = useState('')
  const [numQuestions, setNumQuestions] = useState(10)
  const [difficulty, setDifficulty] = useState('medium')
  const [optionCount, setOptionCount] = useState(4)
  const [generating, setGenerating] = useState(false)
  const [genResult, setGenResult] = useState(null)
  const [genError, setGenError] = useState('')

  const fetchStats = async (userId) => {
    setLoading(true)
    setError('')
    try {
      const res = await axios.get(`${API_BASE_URL}/teacher/stats`, {
        headers: { 'X-TG-Init-Data': window.Telegram?.WebApp?.initData || `DEV_${userId}` },
        params: { t: Date.now() }
      })
      setStats(res.data)
      if (devMode) {
        localStorage.setItem('dev_teacher_tg_id', userId)
      }
    } catch (err) {
      console.error(err)
      setError(err.response?.data?.detail || 'Statistikalarni yuklashda xatolik yuz berdi.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (tgUserId) fetchStats(tgUserId)
  }, [tgUserId])

  const fetchTestDetails = async (testId) => {
    setSelectedTestId(testId)
    setLoadingDetails(true)
    try {
      const res = await axios.get(`${API_BASE_URL}/teacher/tests/${testId}`, {
        headers: { 'X-TG-Init-Data': window.Telegram?.WebApp?.initData || `DEV_${tgUserId}` },
        params: { t: Date.now() }
      })
      setTestDetails(res.data)
    } catch (err) {
      console.error(err)
      alert('Test ma`lumotlarini yuklashda xatolik!')
    } finally {
      setLoadingDetails(false)
    }
  }

  const updateTestStatus = async (newStatus) => {
    if (!testDetails) return
    try {
      await axios.put(`${API_BASE_URL}/teacher/tests/${testDetails.id}/status`, { status: newStatus }, {
        headers: { 'X-TG-Init-Data': window.Telegram?.WebApp?.initData || `DEV_${tgUserId}` }
      })
      setTestDetails({...testDetails, status: newStatus})
      fetchStats(tgUserId) // update background list
    } catch (err) {
      console.error(err)
      alert('Statusni yangilashda xatolik!')
    }
  }

  const handleGenerate = async (e) => {
    e.preventDefault()
    if (!topic.trim()) return
    setGenerating(true)
    setGenError('')
    setGenResult(null)
    try {
      const res = await axios.post(`${API_BASE_URL}/ai/generate`, {
        topic: topic.trim(),
        num_questions: numQuestions,
        difficulty,
        option_count: optionCount
      }, {
        headers: { 'X-TG-Init-Data': window.Telegram?.WebApp?.initData || `DEV_${tgUserId}` }
      })
      setGenResult(res.data)
      setTopic('')
      fetchStats(tgUserId)
    } catch (err) {
      console.error(err)
      setGenError(err.response?.data?.detail || 'Quiz yaratishda xatolik yuz berdi.')
    } finally {
      setGenerating(false)
    }
  }

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
          <h3 style={{ color: 'var(--text-primary)', marginBottom: '8px', fontSize: '20px', fontWeight: '800' }}>Xatolik yuz berdi</h3>
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
        <h1 style={{ fontSize: '18px', fontWeight: '800', color: 'var(--primary)', margin: 0 }}>O'qituvchi</h1>
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
              <button className="btn btn-primary btn-sm" onClick={() => fetchStats(tgUserId)}><RefreshCw size={12}/></button>
            </div>
          </div>
        )}

        {/* --- TAB: DASHBOARD --- */}
        {activeTab === 'dashboard' && (
          <div className="animate-soft-slide">
            <div className="glass-card premium-hero-card" style={{ padding: '24px 20px', marginBottom: '24px', position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: '-40px', right: '-40px', width: '150px', height: '150px', background: 'radial-gradient(circle, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0) 70%)', borderRadius: '50%', filter: 'blur(10px)' }} />
              <h2 style={{ fontSize: '24px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '8px', color: '#fff', textShadow: '0 2px 10px rgba(0,0,0,0.2)' }}>
                <span>Ustoz:</span><span style={{ textDecoration: 'underline', decorationColor: 'rgba(255,255,255,0.8)' }}>{stats.teacher_name}</span>
              </h2>
              <p style={{ opacity: 0.9, fontSize: '13px', marginTop: '6px', color: '#fff' }}>AlKhorazmiyQuiz o'qituvchilar mini-app tahlillari</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '24px' }}>
              <div className="glass-card" style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <Layers size={22} style={{ color: 'var(--primary)', marginBottom: '8px' }} />
                <span style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats.total_tests}</span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600' }}>Testlar</span>
              </div>
              <div className="glass-card" style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <Users size={22} style={{ color: 'var(--success)', marginBottom: '8px' }} />
                <span style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats.total_attempts}</span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600' }}>Urinishlar</span>
              </div>
              <div className="glass-card" style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <Award size={22} style={{ color: 'var(--accent)', marginBottom: '8px' }} />
                <span style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats.pass_rate}%</span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600' }}>O'zlashtirish</span>
              </div>
            </div>

            {stats.tests && stats.tests.length > 0 && (
              <div className="glass-card" style={{ padding: '24px 20px', marginBottom: '24px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <BarChart3 size={16} className="text-primary" /> <span>Testlarning O'rtacha Ko'rsatkichlari (%)</span>
                </h3>
                <div style={{ width: '100%', height: '200px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={stats.tests.slice(0, 5).reverse()}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.15)" />
                      <XAxis dataKey="code" tick={{ fill: 'var(--text-muted)', fontSize: '11px' }} />
                      <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: '11px' }} />
                      <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid var(--border)' }} />
                      <Bar dataKey="average_score" fill="var(--primary)" radius={[4, 4, 0, 0]} label={{ position: 'top', fill: 'var(--text-primary)', fontSize: 10 }} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
            
            {/* Top / Bottom Results */}
            <div className="glass-card" style={{ padding: '24px 20px', marginBottom: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Award size={18} className="text-accent" /><span>Eng Yaxshi Natijalar</span>
              </h3>
              {stats.top_attempts.length === 0 ? <p style={{color: 'var(--text-muted)', fontSize: '12px'}}>Natijalar yo'q</p> : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {stats.top_attempts.map((att, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', borderBottom: '1px solid var(--divider)', padding: '6px 0' }}>
                      <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{att.student_name}</span>
                      <span style={{ color: 'var(--text-muted)', fontSize: '11px', flex: '1', marginLeft: '12px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{att.test_title}</span>
                      <strong style={{ color: 'var(--success)' }}>{att.percent}%</strong>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* --- TAB: TESTS --- */}
        {activeTab === 'tests' && (
          <div className="animate-soft-slide">
            <h2 style={{ fontSize: '20px', fontWeight: '800', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={20} className="text-primary" /> Barcha Testlar
            </h2>
            <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '12px', marginBottom: '12px', scrollbarWidth: 'none' }}>
              {['Barchasi', 'Yangi', 'Jarayonda', 'Tugallangan'].map(filter => (
                <button
                  key={filter}
                  onClick={() => setStatusFilter(filter)}
                  style={{ 
                    padding: '8px 16px', borderRadius: '20px', whiteSpace: 'nowrap', fontSize: '13px', fontWeight: '700', border: '1px solid rgba(255,255,255,0.15)',
                    background: statusFilter === filter ? 'var(--primary)' : 'rgba(0,0,0,0.25)',
                    color: statusFilter === filter ? '#fff' : 'var(--text-primary)',
                    transition: 'all 0.2s'
                  }}
                >
                  {filter}
                </button>
              ))}
            </div>
            {(() => {
              const filtered = (stats.tests || []).filter(test => {
                const status = (test.status || 'draft').toLowerCase()
                if (statusFilter === 'Barchasi') return true
                if (statusFilter === 'Yangi') return status === 'draft'
                if (statusFilter === 'Jarayonda') return status === 'open'
                if (statusFilter === 'Tugallangan') return status === 'closed'
                return true
              })
              if (filtered.length === 0) {
                return <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>Mos keladigan testlar topilmadi.</p>
              }
              return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {filtered.map((test) => {
                    const statusStr = (test.status || 'draft').toLowerCase()
                    return (
                      <div 
                        key={test.id} 
                        onClick={() => fetchTestDetails(test.id)}
                        className="glass-card"
                        style={{ 
                          padding: '16px',
                          cursor: 'pointer'
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                          <h4 style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)' }}>{test.title}</h4>
                          <ChevronRight size={18} style={{ color: 'var(--text-muted)' }} />
                        </div>
                        <div style={{ display: 'flex', gap: '8px', fontSize: '12px' }}>
                          <span className="badge" style={{ background: 'rgba(165, 180, 252, 0.15)', color: 'var(--primary)', fontFamily: 'monospace' }}>{test.code}</span>
                          <span style={{ 
                            background: statusStr === 'open' ? 'rgba(34, 197, 94, 0.2)' : statusStr === 'closed' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                            color: statusStr === 'open' ? '#4ade80' : statusStr === 'closed' ? '#f87171' : '#fbbf24',
                            padding: '2px 8px', borderRadius: '12px', fontWeight: '600'
                          }}>{statusStr.toUpperCase()}</span>
                          <span style={{ color: 'var(--text-muted)' }}>{test.attempts_count} urinish</span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )
            })()}
          </div>
        )}

        {/* --- TAB: AI GENERATOR --- */}
        {activeTab === 'ai' && (
          <div className="animate-soft-slide">
            <div className="glass-card" style={{ padding: '24px 20px', position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: '-20px', right: '-20px', width: '120px', height: '120px', background: 'radial-gradient(circle, rgba(59,79,212,0.15) 0%, rgba(255,255,255,0) 70%)', borderRadius: '50%', filter: 'blur(10px)' }} />
              
              {/* Coming Soon Overlay */}
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'rgba(10, 10, 20, 0.55)',
                backdropFilter: 'blur(8px)',
                WebkitBackdropFilter: 'blur(8px)',
                zIndex: 10,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '24px',
                textAlign: 'center'
              }}>
                <div className="coming-soon-glowing-icon" style={{
                  background: 'rgba(165, 180, 252, 0.12)',
                  border: '1.5px solid rgba(165, 180, 252, 0.4)',
                  borderRadius: '50%',
                  width: '64px',
                  height: '64px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '16px'
                }}>
                  <Wand2 size={30} style={{ color: 'var(--primary)' }} />
                </div>
                <h3 style={{
                  fontSize: '22px',
                  fontWeight: '800',
                  color: '#ffffff',
                  marginBottom: '8px',
                  letterSpacing: '0.5px'
                }}>
                  Coming Soon
                </h3>
                <p style={{
                  fontSize: '13px',
                  color: 'rgba(255, 255, 255, 0.8)',
                  maxWidth: '280px',
                  lineHeight: '1.6',
                  margin: 0
                }}>
                  AI orqali tezkor va oson test yaratish funksiyasi ustida ish olib borilmoqda. Tez kunda faollashadi!
                </p>
              </div>

              <h3 style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <Wand2 size={20} style={{ color: 'var(--primary)' }} /> AI Test Generator
              </h3>

              <div style={{ background: 'rgba(59, 79, 212, 0.05)', borderRadius: '12px', padding: '12px', marginBottom: '16px', border: '1px solid rgba(59, 79, 212, 0.1)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: '600', marginBottom: '6px' }}>
                  <span>AI Limit ({stats.ai_queries_used}/{stats.ai_queries_limit})</span>
                </div>
                <div style={{ height: '6px', background: 'rgba(59, 79, 212, 0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', background: stats.ai_queries_used >= stats.ai_queries_limit ? 'var(--error)' : 'var(--primary)', width: `${Math.min((stats.ai_queries_used / stats.ai_queries_limit) * 100, 100)}%` }} />
                </div>
              </div>

              {genResult && (
                <div className="alert alert-success animate-scale" style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 'bold' }}><CheckCircle size={16} /> Yaratildi!</div>
                  <div style={{ fontSize: '13px', marginTop: '4px' }}>
                    Kod: <strong>{genResult.code}</strong>, Savollar: {genResult.questions_count}
                  </div>
                  <button className="btn btn-ghost btn-sm" onClick={() => setGenResult(null)} style={{ padding: '2px 8px', fontSize: '11px', marginTop: '8px' }}>Yopish</button>
                </div>
              )}
              {genError && (
                <div className="alert alert-error animate-scale" style={{ marginBottom: '16px' }}>
                  <AlertCircle size={16} /> {genError}
                </div>
              )}

              <form onSubmit={handleGenerate} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label" htmlFor="ai-topic">Mavzu:</label>
                  <input type="text" id="ai-topic" className="form-input" placeholder="Masalan: Fizika 7-sinf" value={topic} onChange={(e) => setTopic(e.target.value)} required disabled={generating} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div className="form-group">
                    <label className="form-label">Qiyinchilik:</label>
                    <select className="form-input" value={difficulty} onChange={(e) => setDifficulty(e.target.value)} disabled={generating}>
                      <option value="easy">Oson</option><option value="medium">O'rtacha</option><option value="hard">Qiyin</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Variantlar:</label>
                    <select className="form-input" value={optionCount} onChange={(e) => setOptionCount(parseInt(e.target.value, 10))} disabled={generating}>
                      <option value="2">2 talik</option><option value="4">4 talik</option>
                    </select>
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Savollar soni: {numQuestions} ta</label>
                  <input type="range" min="5" max="20" step="5" value={numQuestions} onChange={(e) => setNumQuestions(parseInt(e.target.value, 10))} style={{ cursor: 'pointer', accentColor: 'var(--primary)' }} disabled={generating} />
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} disabled={generating || !topic.trim() || stats.ai_queries_used >= stats.ai_queries_limit}>
                  {generating ? 'Yaratilmoqda...' : 'AI Test Yaratish'}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>

      {/* --- TEST DETAILS MODAL --- */}
      {selectedTestId && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.6)', zIndex: 100, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', backdropFilter: 'blur(4px)' }}>
          <div className="animate-slide-up" style={{ 
            background: 'rgba(26, 26, 46, 0.95)', 
            width: '100%', 
            maxWidth: '600px', 
            height: '85vh', 
            borderTopLeftRadius: '24px', 
            borderTopRightRadius: '24px', 
            padding: '20px', 
            display: 'flex', 
            flexDirection: 'column',
            borderTop: '1px solid rgba(255, 255, 255, 0.15)',
            borderLeft: '1px solid rgba(255, 255, 255, 0.15)',
            borderRight: '1px solid rgba(255, 255, 255, 0.05)',
            color: 'var(--text-primary)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)' }}>Test Detallari</h3>
              <button onClick={() => setSelectedTestId(null)} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '50%', padding: '6px', cursor: 'pointer', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><X size={20} /></button>
            </div>
            
            {loadingDetails || !testDetails ? (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flex: 1 }}>
                <div className="spinner spinner-primary" />
              </div>
            ) : (
              <div style={{ overflowY: 'auto', flex: 1, paddingRight: '4px' }}>
                <div style={{ background: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)', padding: '16px', borderRadius: '12px', marginBottom: '20px' }}>
                  <h4 style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '8px', color: 'var(--text-primary)' }}>{testDetails.title}</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                    <div><strong>Kod:</strong> <span className="badge" style={{ background: 'rgba(165, 180, 252, 0.2)', color: 'var(--primary)' }}>{testDetails.code}</span></div>
                    <div><strong>Daraja:</strong> {(testDetails.difficulty || '').toUpperCase()}</div>
                    <div><strong>Sana:</strong> {testDetails.created_at}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <strong>Status:</strong> 
                      <select 
                        value={testDetails.status} 
                        onChange={(e) => updateTestStatus(e.target.value)}
                        style={{ 
                          padding: '2px 6px', 
                          borderRadius: '6px', 
                          border: '1px solid rgba(255,255,255,0.2)', 
                          background: 'rgba(0,0,0,0.3)', 
                          color: '#fff', 
                          fontSize: '12px', 
                          outline: 'none' 
                        }}
                      >
                        <option style={{ background: '#1a1a2e', color: '#fff' }} value="draft">Draft (Qoralama)</option>
                        <option style={{ background: '#1a1a2e', color: '#fff' }} value="open">Open (Faol)</option>
                        <option style={{ background: '#1a1a2e', color: '#fff' }} value="closed">Closed (Yopiq)</option>
                      </select>
                    </div>
                  </div>
                </div>

                <h4 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-primary)' }}>
                  <Users size={16} /> Qatnashchilar ({(testDetails.participants || []).length})
                </h4>
                
                {(!testDetails.participants || testDetails.participants.length === 0) ? (
                  <p style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', padding: '20px 0' }}>Hali hech kim yechmadi.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {testDetails.participants.map((p, i) => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.02)' }}>
                        <div>
                          <div style={{ fontWeight: '600', fontSize: '14px', color: 'var(--text-primary)' }}>{p.student_name}</div>
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{p.finished_at}</div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontWeight: '800', color: p.percent >= 50 ? 'var(--success)' : 'var(--error)' }}>{p.percent}%</div>
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{p.score} / {p.max_score}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* --- BOTTOM NAVIGATION --- */}
      <div className="glass-nav" style={{ 
        position: 'fixed', bottom: '16px', left: '16px', right: '16px', 
        borderRadius: '24px', display: 'flex', justifyContent: 'space-around', 
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
          onClick={() => setActiveTab('tests')} 
          className={`nav-item ${activeTab === 'tests' ? 'active' : ''}`}
          style={{ background: 'none', border: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', cursor: 'pointer', flex: 1 }}
        >
          <div className="nav-icon-bg" style={{ padding: '8px 20px', borderRadius: '16px' }}>
            <Layers size={22} strokeWidth={activeTab === 'tests' ? 2.5 : 2} />
          </div>
          <span style={{ fontSize: '11px', fontWeight: activeTab === 'tests' ? '700' : '600' }}>Testlar</span>
        </button>
        <button 
          onClick={() => setActiveTab('ai')} 
          className={`nav-item ${activeTab === 'ai' ? 'active' : ''}`}
          style={{ background: 'none', border: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', cursor: 'pointer', flex: 1 }}
        >
          <div className="nav-icon-bg" style={{ padding: '8px 20px', borderRadius: '16px' }}>
            <Wand2 size={22} strokeWidth={activeTab === 'ai' ? 2.5 : 2} />
          </div>
          <span style={{ fontSize: '11px', fontWeight: activeTab === 'ai' ? '700' : '600' }}>AI Yaratish</span>
        </button>
      </div>
      </div>
    </div>
  )
}
