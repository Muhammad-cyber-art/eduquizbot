import React, { useState, useEffect, useMemo, useCallback } from 'react';
import axios from 'axios';
import { useTelegram } from '../../hooks/useTelegram';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts';
import { 
  Award, BarChart3, Users, ChevronRight, CheckCircle, AlertCircle, RefreshCw, Layers, LayoutDashboard, Wand2, X
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
  const safeTests = useMemo(() => {
    return Array.isArray(stats?.tests) ? stats.tests : [];
  }, [stats?.tests]);

  const topAttempts = useMemo(() => {
    return Array.isArray(stats?.top_attempts) ? stats.top_attempts : [];
  }, [stats?.top_attempts]);

  const chartData = useMemo(() => {
    return safeTests.slice(0, 5).reverse();
  }, [safeTests]);

  return (
    <div className="animate-soft-slide">
      <div className="glass-card premium-hero-card" style={{ padding: '24px 20px', marginBottom: '24px', position: 'relative', overflow: 'hidden' }}>
        <h2 style={{ fontSize: '24px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '8px', color: '#fff', textShadow: '0 2px 10px rgba(0,0,0,0.2)' }}>
          <span>Ustoz:</span><span style={{ textDecoration: 'underline', decorationColor: 'rgba(255,255,255,0.8)' }}>{stats?.teacher_name || 'Noma\'lum'}</span>
        </h2>
        <p style={{ opacity: 0.9, fontSize: '13px', marginTop: '6px', color: '#fff' }}>AlKhorazmiyQuiz o'qituvchilar mini-app tahlillari</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '24px' }}>
        <div className="glass-card" style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Layers size={22} style={{ color: 'var(--primary)', marginBottom: '8px' }} />
          <span style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats?.total_tests || 0}</span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600' }}>Testlar</span>
        </div>
        <div className="glass-card" style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Users size={22} style={{ color: 'var(--success)', marginBottom: '8px' }} />
          <span style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats?.total_attempts || 0}</span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600' }}>Urinishlar</span>
        </div>
        <div className="glass-card" style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Award size={22} style={{ color: 'var(--accent)', marginBottom: '8px' }} />
          <span style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-primary)' }}>{stats?.pass_rate || 0}%</span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600' }}>O'zlashtirish</span>
        </div>
      </div>

      {chartData.length > 0 && (
        <div className="glass-card" style={{ padding: '24px 20px', marginBottom: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <BarChart3 size={16} className="text-primary" /> <span>Testlarning O'rtacha Ko'rsatkichlari (%)</span>
          </h3>
          <div style={{ width: '100%', height: '200px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
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
      
      <div className="glass-card" style={{ padding: '24px 20px', marginBottom: '24px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Award size={18} className="text-accent" /><span>Eng Yaxshi Natijalar</span>
        </h3>
        {topAttempts.length === 0 ? <p style={{color: 'var(--text-muted)', fontSize: '12px'}}>Natijalar yo'q</p> : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {topAttempts.map((att, i) => (
              <div key={att?.id || `top-${i}`} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', borderBottom: '1px solid var(--divider)', padding: '6px 0' }}>
                <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{att?.student_name || 'Noma\'lum'}</span>
                <span style={{ color: 'var(--text-muted)', fontSize: '11px', flex: '1', marginLeft: '12px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{att?.test_title || '---'}</span>
                <span className="badge-percent badge-percent-success">
                  {att?.percent || 0}%
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
});

// 2. Tests Tab
const TestsTab = React.memo(({ stats, onSelectTest }) => {
  const [statusFilter, setStatusFilter] = useState('Barchasi');

  const safeTests = useMemo(() => {
    return Array.isArray(stats?.tests) ? stats.tests : [];
  }, [stats?.tests]);

  const filteredTests = useMemo(() => {
    return safeTests.filter(test => {
      const status = String(test?.status || 'draft').toLowerCase();
      if (statusFilter === 'Barchasi') return true;
      if (statusFilter === 'Yangi') return status === 'draft';
      if (statusFilter === 'Jarayonda') return status === 'open';
      if (statusFilter === 'Tugallangan') return status === 'closed';
      return true;
    });
  }, [safeTests, statusFilter]);

  return (
    <div className="animate-soft-slide">
      <h2 style={{ fontSize: '20px', fontWeight: '800', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Layers size={20} className="text-primary" /> Barcha Testlar
      </h2>
      <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '12px', marginBottom: '12px', scrollbarWidth: 'none' }}>
        {['Barchasi', 'Yangi', 'Jarayonda', 'Tugallangan'].map(filter => (
          <button
            key={filter}
            onClick={() => setStatusFilter(filter)}
            className={`glass-pill ${statusFilter === filter ? 'active' : ''}`}
          >
            {filter}
          </button>
        ))}
      </div>
      
      {filteredTests.length === 0 ? (
        <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>Mos keladigan testlar topilmadi.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {filteredTests.map((test) => {
            const statusStr = String(test?.status || 'draft').toLowerCase();
            return (
              <div 
                key={test.id} 
                onClick={() => onSelectTest(test.id)}
                className="glass-card"
                style={{ padding: '16px', cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <h4 style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)' }}>{test?.title || 'Nomsiz test'}</h4>
                  <ChevronRight size={18} style={{ color: 'var(--text-muted)' }} />
                </div>
                <div style={{ display: 'flex', gap: '8px', fontSize: '12px' }}>
                  <span className="badge" style={{ background: '#1e293b', color: 'var(--primary-light)', border: '1px solid #334155', fontFamily: 'monospace' }}>{test?.code || '---'}</span>
                  <span style={{ 
                    background: '#1e293b',
                    color: statusStr === 'open' ? '#22c55e' : statusStr === 'closed' ? '#ef4444' : '#f59e0b',
                    border: '1.5px solid ' + (statusStr === 'open' ? '#22c55e' : statusStr === 'closed' ? '#ef4444' : '#f59e0b'),
                    padding: '2px 8px', borderRadius: '12px', fontWeight: '800'
                  }}>{statusStr.toUpperCase()}</span>
                  <span style={{ color: 'var(--text-muted)' }}>{test?.attempts_count || 0} urinish</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
});

// 3. AI Generator Tab
const AiGeneratorTab = React.memo(({ stats, tgUserId, fetchStats }) => {
  const [topic, setTopic] = useState('');
  const [numQuestions, setNumQuestions] = useState(10);
  const [difficulty, setDifficulty] = useState('medium');
  const [optionCount, setOptionCount] = useState(4);
  const [generating, setGenerating] = useState(false);
  const [genResult, setGenResult] = useState(null);
  const [genError, setGenError] = useState('');

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!topic.trim()) return;
    
    setGenerating(true);
    setGenError('');
    setGenResult(null);
    
    try {
      const actualInitData = window.Telegram?.WebApp?.initData || (import.meta.env.DEV ? `DEV_${tgUserId}` : '');
      const res = await axios.post(`${API_BASE_URL}/ai/generate`, {
        topic: topic.trim(),
        num_questions: numQuestions,
        difficulty,
        option_count: optionCount
      }, {
        headers: { 'X-TG-Init-Data': actualInitData }
      });
      setGenResult(res.data);
      setTopic('');
      fetchStats(tgUserId);
    } catch (err) {
      console.error(err);
      setGenError(err.response?.data?.detail || 'Quiz yaratishda xatolik yuz berdi.');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="animate-soft-slide">
      <div className="glass-card" style={{ padding: '24px 20px', position: 'relative', overflow: 'hidden' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <Wand2 size={20} style={{ color: 'var(--primary)' }} /> AI Test Generator
        </h3>

        <div style={{ background: 'rgba(59, 79, 212, 0.05)', borderRadius: '12px', padding: '12px', marginBottom: '16px', border: '1px solid rgba(59, 79, 212, 0.1)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: '600', marginBottom: '6px' }}>
            <span>AI Limit ({stats?.ai_queries_used || 0}/{stats?.ai_queries_limit || 10})</span>
          </div>
          <div style={{ height: '6px', background: 'rgba(59, 79, 212, 0.1)', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ height: '100%', background: (stats?.ai_queries_used || 0) >= (stats?.ai_queries_limit || 10) ? 'var(--error)' : 'var(--primary)', width: `${Math.min(((stats?.ai_queries_used || 0) / (stats?.ai_queries_limit || 10)) * 100, 100)}%` }} />
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
          <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} disabled={generating || !topic.trim() || (stats?.ai_queries_used || 0) >= (stats?.ai_queries_limit || 10)}>
            {generating ? 'Yaratilmoqda...' : 'AI Test Yaratish'}
          </button>
        </form>
      </div>
    </div>
  );
});

// --- Test Details Modal Component ---
const TestDetailsModal = React.memo(({ testId, tgUserId, onClose, onUpdateStatus }) => {
  const [testDetails, setTestDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    
    const fetchDetails = async () => {
      try {
        const actualInitData = window.Telegram?.WebApp?.initData || (import.meta.env.DEV ? `DEV_${tgUserId}` : '');
        const res = await axios.get(`${API_BASE_URL}/teacher/tests/${testId}`, {
          headers: { 'X-TG-Init-Data': actualInitData },
          params: { t: Date.now() },
          signal: controller.signal
        });
        setTestDetails(res.data);
      } catch (err) {
        if (axios.isCancel(err)) return;
        console.error(err);
        alert('Test ma`lumotlarini yuklashda xatolik!');
      } finally {
        setLoading(false);
      }
    };
    
    fetchDetails();
    return () => controller.abort();
  }, [testId, tgUserId]);

  const handleStatusChange = async (e) => {
    const newStatus = e.target.value;
    try {
      const actualInitData = window.Telegram?.WebApp?.initData || (import.meta.env.DEV ? `DEV_${tgUserId}` : '');
      await axios.put(`${API_BASE_URL}/teacher/tests/${testId}/status`, { status: newStatus }, {
        headers: { 'X-TG-Init-Data': actualInitData }
      });
      setTestDetails(prev => ({ ...prev, status: newStatus }));
      onUpdateStatus(); // triggers background fetch
    } catch (err) {
      console.error(err);
      alert('Statusni yangilashda xatolik!');
    }
  };

  const safeParticipants = useMemo(() => {
    return Array.isArray(testDetails?.participants) ? testDetails.participants.slice(0, 50) : [];
  }, [testDetails?.participants]);

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.6)', zIndex: 100, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', backdropFilter: 'blur(4px)' }}>
      <div className="animate-slide-up" style={{ 
        background: 'rgba(26, 26, 46, 0.95)', width: '100%', maxWidth: '600px', height: '85vh', 
        borderTopLeftRadius: '24px', borderTopRightRadius: '24px', padding: '20px', 
        display: 'flex', flexDirection: 'column',
        borderTop: '1px solid rgba(255, 255, 255, 0.15)',
        borderLeft: '1px solid rgba(255, 255, 255, 0.15)',
        borderRight: '1px solid rgba(255, 255, 255, 0.05)',
        color: 'var(--text-primary)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)' }}>Test Detallari</h3>
          <button onClick={onClose} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '50%', padding: '6px', cursor: 'pointer', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><X size={20} /></button>
        </div>
        
        {loading || !testDetails ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flex: 1 }}>
            <div className="spinner spinner-primary" />
          </div>
        ) : (
          <div style={{ overflowY: 'auto', flex: 1, paddingRight: '4px' }}>
            <div style={{ background: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)', padding: '16px', borderRadius: '12px', marginBottom: '20px' }}>
              <h4 style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '8px', color: 'var(--text-primary)' }}>{testDetails.title}</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                <div><strong>Kod:</strong> <span className="badge" style={{ background: '#1e293b', color: 'var(--primary-light)', border: '1px solid #334155' }}>{testDetails.code}</span></div>
                <div><strong>Daraja:</strong> {String(testDetails.difficulty || '').toUpperCase()}</div>
                <div><strong>Sana:</strong> {testDetails.created_at}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <strong>Status:</strong> 
                  <select 
                    value={testDetails.status || 'draft'} 
                    onChange={handleStatusChange}
                    style={{ 
                      padding: '2px 6px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.2)', 
                      background: 'rgba(0,0,0,0.3)', color: '#fff', fontSize: '12px', outline: 'none' 
                    }}
                  >
                    <option style={{ background: '#1a1a2e', color: '#fff' }} value="draft">Draft</option>
                    <option style={{ background: '#1a1a2e', color: '#fff' }} value="open">Open</option>
                    <option style={{ background: '#1a1a2e', color: '#fff' }} value="closed">Closed</option>
                  </select>
                </div>
              </div>
            </div>

            <h4 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-primary)' }}>
              <Users size={16} /> Qatnashchilar ({(testDetails.participants || []).length})
            </h4>
            
            {safeParticipants.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', padding: '20px 0' }}>Hali hech kim yechmadi.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {safeParticipants.map((p, i) => (
                  <div key={p?.id || i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.02)' }}>
                    <div>
                      <div style={{ fontWeight: '600', fontSize: '14px', color: 'var(--text-primary)' }}>{p?.student_name || 'Noma\'lum'}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{p?.finished_at || '---'}</div>
                    </div>
                    <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                      <span className={`badge-percent ${(p?.percent || 0) >= 50 ? 'badge-percent-success' : 'badge-percent-error'}`}>
                        {p?.percent || 0}%
                      </span>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{p?.score || 0} / {p?.max_score || 0}</div>
                    </div>
                  </div>
                ))}
                {(testDetails.participants || []).length > 50 && (
                   <p style={{ color: 'var(--text-muted)', fontSize: '12px', textAlign: 'center', marginTop: '10px' }}>Faqat oxirgi 50 ta natija ko'rsatilmoqda.</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
});

// --- Main Application Component ---
export default function TeacherWebApp() {
  const { tg, user, initData } = useTelegram();

  const [tgUserId, setTgUserId] = useState(() => {
    // DEV check
    if (import.meta.env.DEV) {
      return localStorage.getItem('dev_teacher_tg_id') || '1681742626';
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

  // Test Details Modal
  const [selectedTestId, setSelectedTestId] = useState(null);

  const fetchStats = useCallback(async (userId, signal) => {
    if (!userId) {
       setError("Foydalanuvchi IDsi topilmadi. Iltimos, Telegram orqali kiring.");
       setLoading(false);
       return;
    }
    setLoading(true);
    setError('');
    
    try {
      const actualInitData = initData || (import.meta.env.DEV ? `DEV_${userId}` : '');
      const res = await axios.get(`${API_BASE_URL}/teacher/stats`, {
        headers: { 'X-TG-Init-Data': actualInitData },
        params: { t: Date.now() },
        signal: signal
      });
      setStats(res.data);
      if (import.meta.env.DEV) {
        localStorage.setItem('dev_teacher_tg_id', userId);
      }
    } catch (err) {
      if (axios.isCancel(err)) return;
      console.error(err);
      const errDetail = err.response?.data?.detail || '';
      const fallbackMsg = `Xatolik: ${err.message} (${err.name}). Nginx: 200 OK. Localtunnel/CORS issue?`;
      setError(errDetail || fallbackMsg);
    } finally {
      setLoading(false);
    }
  }, [initData]);

  useEffect(() => {
    if (!initData && !import.meta.env.DEV) return;
    const controller = new AbortController();
    fetchStats(tgUserId, controller.signal);
    return () => controller.abort();
  }, [tgUserId, fetchStats, initData]);

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

          {activeTab === 'dashboard' && <DashboardTab stats={stats} />}
          {activeTab === 'tests' && <TestsTab stats={stats} onSelectTest={setSelectedTestId} />}
          {activeTab === 'ai' && <AiGeneratorTab stats={stats} tgUserId={tgUserId} fetchStats={fetchStats} />}
        </div>

        {selectedTestId && (
          <TestDetailsModal 
            testId={selectedTestId} 
            tgUserId={tgUserId} 
            onClose={() => setSelectedTestId(null)} 
            onUpdateStatus={() => fetchStats(tgUserId)}
          />
        )}

        <div className="glass-nav" style={{ 
          position: 'fixed', bottom: '16px', left: '16px', right: '16px', 
          borderRadius: '30px', display: 'flex', justifyContent: 'space-around', 
          padding: '12px 8px', zIndex: 50
        }}>
          {[
            { id: 'dashboard', icon: LayoutDashboard, label: 'Asosiy' },
            { id: 'tests', icon: Layers, label: 'Testlar' },
            { id: 'ai', icon: Wand2, label: 'AI Yaratish' }
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
