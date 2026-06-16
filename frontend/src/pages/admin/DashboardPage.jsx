import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { analyticsAPI } from '../../api'
import { useLang } from '../../contexts/LangContext'
import { 
  Users, 
  UserCheck, 
  GraduationCap, 
  BookOpen, 
  Award, 
  ClipboardList, 
  ArrowRight,
  RefreshCw
} from 'lucide-react'

export default function DashboardPage() {
  const { t } = useLang()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchStats = async (signal) => {
    setLoading(true)
    setError('')
    try {
      const response = await analyticsAPI.dashboard({ signal })
      setStats(response.data)
    } catch (err) {
      if (err.name === 'CanceledError' || err.code === 'ERR_CANCELED') return
      console.error(err)
      setError('Failed to fetch dashboard statistics.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const controller = new AbortController()
    fetchStats(controller.signal)
    return () => controller.abort()
  }, [])

  if (loading) {
    return (
      <div className="admin-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '80vh' }}>
        <div className="spinner spinner-primary" style={{ width: '40px', height: '40px' }} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="admin-page">
        <div className="alert alert-error" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{error}</span>
          <button className="btn btn-primary btn-sm" onClick={fetchStats}>
            <RefreshCw size={14} />
            <span>Retry</span>
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="admin-page animate-fade">
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">{t('dashboard')}</h1>
          <p className="page-sub">AlKhorazmiyQuiz platform analytics and overview</p>
        </div>
        <button 
          className="btn btn-ghost" 
          onClick={() => fetchStats()}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', border: '1px solid var(--border)' }}
          id="refresh-stats-btn"
        >
          <RefreshCw size={14} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid animate-fade-up">
        {/* Total Users */}
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(59, 79, 212, 0.08)', color: 'var(--primary)' }}>
            <Users size={22} />
          </div>
          <div className="stat-value">{stats?.total_users ?? 0}</div>
          <div className="stat-label">{t('totalUsers')}</div>
        </div>

        {/* Teachers */}
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(34, 197, 94, 0.08)', color: 'var(--success)' }}>
            <GraduationCap size={22} />
          </div>
          <div className="stat-value">{stats?.total_teachers ?? 0}</div>
          <div className="stat-label">{t('teachers')}</div>
        </div>

        {/* Students */}
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(107, 127, 232, 0.08)', color: 'var(--primary-light)' }}>
            <UserCheck size={22} />
          </div>
          <div className="stat-value">{stats?.total_students ?? 0}</div>
          <div className="stat-label">{t('students')}</div>
        </div>

        {/* Total Tests */}
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(245, 166, 35, 0.08)', color: 'var(--accent)' }}>
            <BookOpen size={22} />
          </div>
          <div className="stat-value">{stats?.total_tests ?? 0}</div>
          <div className="stat-label">{t('tests')}</div>
        </div>

        {/* Quiz Attempts */}
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(142, 89, 182, 0.08)', color: '#8E59B6' }}>
            <Award size={22} />
          </div>
          <div className="stat-value">{stats?.total_attempts ?? 0}</div>
          <div className="stat-label">{t('attempts')}</div>
        </div>

        {/* Pending Requests */}
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(239, 68, 68, 0.08)', color: 'var(--error)' }}>
            <ClipboardList size={22} />
          </div>
          <div className="stat-value">{stats?.pending_requests ?? 0}</div>
          <div className="stat-label">{t('pendingRequests')}</div>
        </div>
      </div>

      {/* Quick Actions & Short Info */}
      <div 
        style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
          gap: '24px', 
          marginTop: '32px' 
        }}
        className="animate-fade-up delay-100"
      >
        {/* Pending Requests Widget */}
        <div className="card" style={{ padding: '24px', background: '#fff' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ClipboardList size={18} className="text-primary" />
            <span>Teacher Requests Status</span>
          </h3>
          {stats?.pending_requests > 0 ? (
            <div>
              <div className="alert alert-info animate-pulse" style={{ marginBottom: '20px' }}>
                You have {stats.pending_requests} pending access requests waiting for review!
              </div>
              <Link to="/admin/requests" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
                <span>Review Requests</span>
                <ArrowRight size={16} />
              </Link>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '20px 0', color: 'var(--text-muted)' }}>
              <p style={{ fontSize: '32px', marginBottom: '10px' }}>✅</p>
              <p style={{ fontSize: '14px' }}>All requests have been reviewed!</p>
            </div>
          )}
        </div>

        {/* Shortcuts / Overview */}
        <div className="card" style={{ padding: '24px', background: '#fff' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            🚀 Shortcuts
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <Link to="/admin/users" className="btn btn-ghost" style={{ justifyContent: 'space-between', border: '1px solid var(--border)', padding: '12px 16px' }}>
              <span>Manage Bot Users</span>
              <ArrowRight size={14} />
            </Link>
            <Link to="/admin/analytics" className="btn btn-ghost" style={{ justifyContent: 'space-between', border: '1px solid var(--border)', padding: '12px 16px' }}>
              <span>View Interactive Analytics Charts</span>
              <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
