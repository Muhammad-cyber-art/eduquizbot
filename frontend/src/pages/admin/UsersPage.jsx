import { useState, useEffect, useCallback } from 'react'
import { usersAPI } from '../../api'
import { useLang } from '../../contexts/LangContext'
import { Search, RefreshCw, GraduationCap, UserCheck, ShieldAlert, Calendar } from 'lucide-react'

export default function UsersPage() {
  const { t } = useLang()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [roleFilter, setRoleFilter] = useState('')

  // Edit limits modal states
  const [limitsModalOpen, setLimitsModalOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  const [maxTests, setMaxTests] = useState(5)
  const [maxStudents, setMaxStudents] = useState(50)
  const [aiQueriesLimit, setAiQueriesLimit] = useState(10)
  const [aiQueriesUsed, setAiQueriesUsed] = useState(0)
  const [is_active, setIsActive] = useState(true)
  const [expiresAt, setExpiresAt] = useState('')


  const fetchUsers = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = {}
      if (roleFilter) params.role = roleFilter
      if (searchTerm.trim()) params.search = searchTerm.trim()

      const response = await usersAPI.list(params)
      setUsers(response.data)
    } catch (err) {
      console.error(err)
      setError('Failed to fetch bot users.')
    } finally {
      setLoading(false)
    }
  }, [searchTerm, roleFilter])

  useEffect(() => {
    // Implement standard delay to debounce queries
    const timer = setTimeout(() => {
      fetchUsers()
    }, 400)
    return () => clearTimeout(timer)
  }, [searchTerm, roleFilter, fetchUsers])

  const openLimitsModal = (user) => {
    setSelectedUser(user)
    setMaxTests(user.max_tests)
    setMaxStudents(user.max_students)
    setAiQueriesLimit(user.ai_queries_limit ?? 10)
    setAiQueriesUsed(user.ai_queries_used ?? 0)
    setIsActive(user.is_active)
    setExpiresAt(user.expires_at ? user.expires_at.split('T')[0] : '')
    setLimitsModalOpen(true)
  }


  const handleUpdateLimits = async () => {
    if (!selectedUser) return
    try {
      const data = {
        max_tests: maxTests,
        max_students: maxStudents,
        ai_queries_limit: aiQueriesLimit,
        ai_queries_used: aiQueriesUsed,
        is_active: is_active,
        expires_at: expiresAt ? new Date(expiresAt).toISOString() : null
      }

      await usersAPI.updateLimits(selectedUser.id, data)
      alert(t('limitsUpdated'))
      setLimitsModalOpen(false)
      fetchUsers()
    } catch (err) {
      console.error(err)
      alert('Failed to update limits.')
    }
  }

  const getRoleBadge = (role) => {
    switch (role?.toLowerCase()) {
      case 'teacher':
        return (
          <span className="badge badge-teacher">
            <GraduationCap size={12} />
            <span style={{ marginLeft: '4px' }}>Teacher</span>
          </span>
        )
      case 'student':
        return (
          <span className="badge badge-student">
            <UserCheck size={12} />
            <span style={{ marginLeft: '4px' }}>Student</span>
          </span>
        )
      case 'admin':
        return (
          <span className="badge badge-admin">
            <ShieldAlert size={12} />
            <span style={{ marginLeft: '4px' }}>Admin</span>
          </span>
        )
      default:
        return <span className="badge">{role || 'User'}</span>
    }
  }

  const formatDate = (isoString) => {
    if (!isoString) return '—'
    const date = new Date(isoString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="admin-page animate-fade">
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">{t('usersTitle')}</h1>
          <p className="page-sub">{t('usersSub')}</p>
        </div>
        <button 
          className="btn btn-ghost" 
          onClick={fetchUsers}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', border: '1px solid var(--border)' }}
          id="refresh-users-btn"
        >
          <RefreshCw size={14} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Search and Filters Bar */}
      <div 
        className="card" 
        style={{ 
          background: '#fff', 
          padding: '16px 20px', 
          marginBottom: '24px',
          display: 'flex',
          gap: '16px',
          alignItems: 'center',
          flexWrap: 'wrap'
        }}
      >
        {/* Search */}
        <div className="search-wrap" style={{ flex: '1', minWidth: '240px' }}>
          <Search className="search-icon" />
          <input
            id="user-search-input"
            type="text"
            className="form-input"
            placeholder={t('searchPlaceholder')}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ width: '100%' }}
          />
        </div>

        {/* Role Select Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label className="form-label" style={{ marginBottom: '0', whiteSpace: 'nowrap' }} htmlFor="user-role-select">
            {t('roleFilter')}:
          </label>
          <select
            id="user-role-select"
            className="form-input"
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            style={{ padding: '8px 36px 8px 12px', background: 'var(--bg-page)', cursor: 'pointer' }}
          >
            <option value="">{t('all')}</option>
            <option value="teacher">Teacher</option>
            <option value="student">Student</option>
            <option value="admin">Admin</option>
          </select>
        </div>
      </div>

      {/* Users Table / Empty States */}
      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '80px 0' }}>
          <div className="spinner spinner-primary" style={{ width: '30px', height: '30px' }} />
        </div>
      ) : error ? (
        <div className="alert alert-error">{error}</div>
      ) : users.length === 0 ? (
        <div className="card empty-state animate-scale" style={{ background: '#fff' }}>
          <span className="emoji">👤</span>
          <h3>{t('noUsers')}</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '6px' }}>
            Try matching a different search term or role selection
          </p>
        </div>
      ) : (
        <div className="table-card animate-fade-up">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>{t('name')}</th>
                  <th>{t('tgId')}</th>
                  <th>{t('role')}</th>
                  <th>{t('maxTests')}</th>
                  <th>{t('maxStudents')}</th>
                  <th>{t('aiQueries')}</th>
                  <th>Status</th>
                  <th>{t('expiryDate')}</th>

                  <th>Language</th>
                  <th>{t('joinedAt')}</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td>{user.id}</td>
                    <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{user.full_name || '—'}</td>
                    <td style={{ fontFamily: 'monospace', fontSize: '13px' }}>{user.tg_user_id}</td>
                    <td>{getRoleBadge(user.role)}</td>
                    
                    {user.role === 'teacher' ? (
                      <>
                        <td style={{ fontWeight: '600' }}>{user.max_tests}</td>
                        <td style={{ fontWeight: '600' }}>{user.max_students}</td>
                        <td style={{ fontWeight: '600' }}>{user.ai_queries_used} / {user.ai_queries_limit}</td>
                        <td>
                          <span className={`badge ${user.is_active ? 'badge-approved' : 'badge-rejected'}`}>
                            {user.is_active ? t('active') : t('inactive')}
                          </span>
                        </td>
                        <td style={{ fontSize: '13px' }}>{user.expires_at ? formatDate(user.expires_at) : 'Never'}</td>
                      </>
                    ) : (
                      <>
                        <td style={{ color: 'var(--text-muted)' }}>—</td>
                        <td style={{ color: 'var(--text-muted)' }}>—</td>
                        <td style={{ color: 'var(--text-muted)' }}>—</td>
                        <td>
                          <span className="badge badge-approved">{t('active')}</span>
                        </td>
                        <td style={{ color: 'var(--text-muted)' }}>—</td>
                      </>
                    )}

                    
                    <td style={{ textTransform: 'uppercase', fontSize: '12px', fontWeight: '700' }}>
                      <span 
                        style={{ 
                          background: 'var(--bg-page)', 
                          padding: '2px 8px', 
                          borderRadius: '4px',
                          border: '1px solid var(--border)' 
                        }}
                      >
                        {user.lang_code || 'uz'}
                      </span>
                    </td>
                    <td style={{ fontSize: '13px' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)' }}>
                        <Calendar size={13} className="text-muted" />
                        <span>{formatDate(user.created_at)}</span>
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      {user.role === 'teacher' && (
                        <button 
                          className="btn btn-ghost btn-sm"
                          style={{ border: '1px solid var(--border)', display: 'inline-flex', gap: '4px' }}
                          onClick={() => openLimitsModal(user)}
                          id={`edit-limits-${user.id}`}
                        >
                          <span>{t('editLimits')}</span>
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ===== EDIT TEACHER LIMITS DIALOG MODAL ===== */}
      {limitsModalOpen && selectedUser && (
        <div className="modal-overlay">
          <div className="modal animate-scale" style={{ maxWidth: '420px' }}>
            <h3 className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <GraduationCap size={20} className="text-primary" />
              <span>{t('teacherLimits')}</span>
            </h3>
            
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
              Edit limits and status for <strong>{selectedUser.full_name || 'Teacher'}</strong>:
            </p>

            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label className="form-label" htmlFor="edit-max-tests">{t('maxTests')}</label>
              <input
                type="number"
                id="edit-max-tests"
                className="form-input"
                value={maxTests}
                onChange={(e) => setMaxTests(parseInt(e.target.value, 10))}
                min="1"
                style={{ width: '100%', padding: '10px 14px' }}
                required
              />
            </div>

            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label className="form-label" htmlFor="edit-max-students">{t('maxStudents')}</label>
              <input
                type="number"
                id="edit-max-students"
                className="form-input"
                value={maxStudents}
                onChange={(e) => setMaxStudents(parseInt(e.target.value, 10))}
                min="1"
                style={{ width: '100%', padding: '10px 14px' }}
                required
              />
            </div>

            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label className="form-label" htmlFor="edit-ai-limit">{t('aiQueriesLimit')}</label>
              <input
                type="number"
                id="edit-ai-limit"
                className="form-input"
                value={aiQueriesLimit}
                onChange={(e) => setAiQueriesLimit(parseInt(e.target.value, 10))}
                min="0"
                style={{ width: '100%', padding: '10px 14px' }}
                required
              />
            </div>

            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label className="form-label" htmlFor="edit-ai-used">{t('aiQueriesUsed')}</label>
              <input
                type="number"
                id="edit-ai-used"
                className="form-input"
                value={aiQueriesUsed}
                onChange={(e) => setAiQueriesUsed(parseInt(e.target.value, 10))}
                min="0"
                style={{ width: '100%', padding: '10px 14px' }}
                required
              />
            </div>

            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label className="form-label" htmlFor="edit-expiry">{t('expiryDate')}</label>

              <input
                type="date"
                id="edit-expiry"
                className="form-input"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
                style={{ width: '100%', padding: '10px 14px' }}
              />
            </div>

            <div className="form-group" style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <input
                type="checkbox"
                id="edit-active"
                checked={is_active}
                onChange={(e) => setIsActive(e.target.checked)}
                style={{ width: '18px', height: '18px', cursor: 'pointer' }}
              />
              <label htmlFor="edit-active" style={{ cursor: 'pointer', fontWeight: '600', marginBottom: '0' }}>
                {t('active')}
              </label>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button 
                className="btn btn-ghost" 
                onClick={() => setLimitsModalOpen(false)}
                id="cancel-limits-btn"
              >
                {t('cancel')}
              </button>
              <button 
                className="btn btn-primary" 
                onClick={handleUpdateLimits}
                id="save-limits-btn"
              >
                {t('save')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
