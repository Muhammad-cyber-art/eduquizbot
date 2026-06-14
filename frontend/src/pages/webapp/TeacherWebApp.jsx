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
          <h3 style={{ color: 'var(--text-primary)', marginBottom: '8px' }}>Xatolik yuz berdi</h3>
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
        <h1 style={{ fontSize: '18px', fontWeight: '800', color: 'var(--primary)', margin: 0 }}>O'qituvchi</h1>
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
            <div style={{ background: 'linear-gradient(135deg, var(--primary) 0%, #2A3BAA 100%)', borderRadius: '16px', padding: '24px 20px', color: '#fff', marginBottom: '20px', boxShadow: '0 10px 25px rgba(59, 79, 212, 0.2)' }}>
              <h2 style={{ fontSize: '22px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>Ustoz:</span><span style={{ textDecoration: 'underline', decorationColor: 'var(--accent)' }}>{stats.teacher_name}</span>
              </h2>
              <p style={{ opacity: 0.8, fontSize: '13px', marginTop: '4px' }}>AlKhorazmiyQuiz o'qituvchilar mini-app tahlillari</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '20px' }}>
              <div className="card" style={{ padding: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <Layers size={18} style={{ color: 'var(--primary)', marginBottom: '4px' }} />
                <span style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats.total_tests}</span>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Testlar</span>
              </div>
              <div className="card" style={{ padding: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <Users size={18} style={{ color: 'var(--success)', marginBottom: '4px' }} />
                <span style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats.total_attempts}</span>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Urinishlar</span>
              </div>
              <div className="card" style={{ padding: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <Award size={18} style={{ color: 'var(--accent)', marginBottom: '4px' }} />
                <span style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats.pass_rate}%</span>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>O'zlashtirish</span>
              </div>
            </div>

            {stats.tests && stats.tests.length > 0 && (
              <div className="card" style={{ padding: '20px', marginBottom: '24px' }}>
                <h3 style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <BarChart3 size={16} className="text-primary" /> <span>Testlarning O'rtacha Ko'rsatkichlari (%)</span>
                </h3>
                <div style={{ width: '100%', height: '200px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={stats.tests.slice(0, 5).reverse()}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
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
            <div className="card" style={{ padding: '20px', marginBottom: '24px' }}>
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
          <div className="animate-fade">
            <h2 style={{ fontSize: '18px', fontWeight: '800', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={20} className="text-primary" /> Barcha Testlar
            </h2>
            {stats.tests.length === 0 ? (
              <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>Hozircha testlar yo'q.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {stats.tests.map((test) => (
                  <div 
                    key={test.id} 
                    onClick={() => fetchTestDetails(test.id)}
                    style={{ 
                      padding: '16px', background: '#FFF', border: '1.5px solid var(--border)', borderRadius: '12px',
                      cursor: 'pointer', transition: 'all 0.2s', boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <h4 style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)' }}>{test.title}</h4>
                      <ChevronRight size={18} style={{ color: 'var(--text-muted)' }} />
                    </div>
                    <div style={{ display: 'flex', gap: '8px', fontSize: '12px' }}>
                      <span className="badge" style={{ background: '#EEF0FF', color: 'var(--primary)', fontFamily: 'monospace' }}>{test.code}</span>
                      <span style={{ 
                        background: test.status === 'open' ? '#DCFCE7' : test.status === 'closed' ? '#FEE2E2' : '#FEF9C3',
                        color: test.status === 'open' ? '#166534' : test.status === 'closed' ? '#991B1B' : '#A16207',
                        padding: '2px 8px', borderRadius: '12px', fontWeight: '600'
                      }}>{test.status.toUpperCase()}</span>
                      <span style={{ color: 'var(--text-muted)' }}>{test.attempts_count} urinish</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* --- TAB: AI GENERATOR --- */}
        {activeTab === 'ai' && (
          <div className="animate-fade">
            <div className="card" style={{ padding: '20px', position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: '-20px', right: '-20px', width: '80px', height: '80px', background: 'radial-gradient(circle, rgba(59,79,212,0.15) 0%, rgba(255,255,255,0) 70%)', borderRadius: '50%' }} />
              
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
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 100, display: 'flex', alignItems: 'flex-end', justifyContent: 'center' }}>
          <div className="animate-slide-up" style={{ background: '#FFF', width: '100%', maxWidth: '600px', height: '85vh', borderTopLeftRadius: '24px', borderTopRightRadius: '24px', padding: '20px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '800' }}>Test Detallari</h3>
              <button onClick={() => setSelectedTestId(null)} style={{ background: '#F3F4F6', border: 'none', borderRadius: '50%', padding: '6px', cursor: 'pointer' }}><X size={20} /></button>
            </div>
            
            {loadingDetails || !testDetails ? (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flex: 1 }}>
                <div className="spinner spinner-primary" />
              </div>
            ) : (
              <div style={{ overflowY: 'auto', flex: 1, paddingRight: '4px' }}>
                <div style={{ background: '#F8F9FE', padding: '16px', borderRadius: '12px', marginBottom: '20px' }}>
                  <h4 style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '8px' }}>{testDetails.title}</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '13px' }}>
                    <div><strong>Kod:</strong> <span className="badge" style={{ background: '#EEF0FF', color: 'var(--primary)' }}>{testDetails.code}</span></div>
                    <div><strong>Daraja:</strong> {testDetails.difficulty.toUpperCase()}</div>
                    <div><strong>Sana:</strong> {testDetails.created_at}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <strong>Status:</strong> 
                      <select 
                        value={testDetails.status} 
                        onChange={(e) => updateTestStatus(e.target.value)}
                        style={{ padding: '2px 4px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '12px', outline: 'none' }}
                      >
                        <option value="draft">Draft (Qoralama)</option>
                        <option value="open">Open (Faol)</option>
                        <option value="closed">Closed (Yopiq)</option>
                      </select>
                    </div>
                  </div>
                </div>

                <h4 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Users size={16} /> Qatnashchilar ({testDetails.participants.length})
                </h4>
                
                {testDetails.participants.length === 0 ? (
                  <p style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', padding: '20px 0' }}>Hali hech kim yechmadi.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {testDetails.participants.map((p, i) => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', border: '1px solid var(--border)', borderRadius: '8px' }}>
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
          onClick={() => setActiveTab('tests')} 
          style={{ background: 'none', border: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', cursor: 'pointer', color: activeTab === 'tests' ? 'var(--primary)' : 'var(--text-muted)' }}
        >
          <Layers size={22} strokeWidth={activeTab === 'tests' ? 2.5 : 2} />
          <span style={{ fontSize: '10px', fontWeight: activeTab === 'tests' ? '700' : '500' }}>Testlar</span>
        </button>
        <button 
          onClick={() => setActiveTab('ai')} 
          style={{ background: 'none', border: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', cursor: 'pointer', color: activeTab === 'ai' ? 'var(--primary)' : 'var(--text-muted)' }}
        >
          <Wand2 size={22} strokeWidth={activeTab === 'ai' ? 2.5 : 2} />
          <span style={{ fontSize: '10px', fontWeight: activeTab === 'ai' ? '700' : '500' }}>AI Yaratish</span>
        </button>
      </div>
    </div>
  )
}
