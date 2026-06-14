import { useState, useEffect } from 'react'
import { requestsAPI } from '../../api'
import { useLang } from '../../contexts/LangContext'
import { 
  Check, 
  X, 
  Copy, 
  ClipboardCheck, 
  RefreshCw, 
  Clock, 
  UserCheck, 
  UserX
} from 'lucide-react'

export default function RequestsPage() {
  const { t } = useLang()
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [statusFilter, setStatusFilter] = useState('pending') // default to pending
  const [selectedRequest, setSelectedRequest] = useState(null) // for password modal
  const [copied, setCopied] = useState(false)

  // SaaS Teacher Limits Modal States
  const [assignModalOpen, setAssignModalOpen] = useState(false)
  const [assignRequestId, setAssignRequestId] = useState(null)
  const [maxTests, setMaxTests] = useState(5)
  const [maxStudents, setMaxStudents] = useState(50)
  const [aiQueriesLimit, setAiQueriesLimit] = useState(10)
  const [expiresAt, setExpiresAt] = useState('')


  const fetchRequests = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await requestsAPI.list(statusFilter)
      setRequests(response.data)
    } catch (err) {
      console.error(err)
      setError('Failed to load access requests.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRequests()
  }, [statusFilter])

  // Open the teacher limits setup modal
  const startApprovalFlow = (requestId) => {
    setAssignRequestId(requestId)
    setMaxTests(5)
    setMaxStudents(50)
    setAiQueriesLimit(10)
    setExpiresAt('')
    setAssignModalOpen(true)
  }


  const handleApprove = async () => {
    if (!assignRequestId) return
    
    setAssignModalOpen(false)
    try {
      const limits = {
        max_tests: maxTests,
        max_students: maxStudents,
        ai_queries_limit: aiQueriesLimit,
      }

      if (expiresAt) {
        limits.expires_at = new Date(expiresAt).toISOString()
      }
      const response = await requestsAPI.approve(assignRequestId, limits)
      const data = response.data
      
      // Open credentials popup modal
      setSelectedRequest({
        id: assignRequestId,
        password: data.password
      })
      fetchRequests()
    } catch (err) {
      console.error(err)
      alert('Failed to approve request. Please try again.')
    } finally {
      setAssignRequestId(null)
    }
  }

  const handleReject = async (id) => {
    if (!window.confirm('Are you sure you want to reject this request?')) return
    try {
      await requestsAPI.reject(id)
      fetchRequests()
    } catch (err) {
      console.error(err)
      alert('Failed to reject request.')
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '—'
    const d = new Date(dateStr)
    return d.toLocaleString()
  }

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'pending': return 'badge-pending'
      case 'approved': return 'badge-approved'
      case 'rejected': return 'badge-rejected'
      default: return ''
    }
  }

  return (
    <div className="admin-page animate-fade">
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">{t('reqTitleAdmin')}</h1>
          <p className="page-sub">{t('reqSubAdmin')}</p>
        </div>
        <button 
          className="btn btn-ghost" 
          onClick={fetchRequests}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', border: '1px solid var(--border)' }}
          id="refresh-requests-btn"
        >
          <RefreshCw size={14} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter Chips */}
      <div style={{ marginBottom: '24px' }}>
        <div className="filter-chips">
          <button 
            className={`chip ${statusFilter === 'all' ? 'active' : ''}`}
            onClick={() => setStatusFilter('all')}
            id="filter-all"
          >
            {t('all')}
          </button>
          <button 
            className={`chip ${statusFilter === 'pending' ? 'active' : ''}`}
            onClick={() => setStatusFilter('pending')}
            id="filter-pending"
          >
            {t('pending')}
          </button>
          <button 
            className={`chip ${statusFilter === 'approved' ? 'active' : ''}`}
            onClick={() => setStatusFilter('approved')}
            id="filter-approved"
          >
            {t('approved')}
          </button>
          <button 
            className={`chip ${statusFilter === 'rejected' ? 'active' : ''}`}
            onClick={() => setStatusFilter('rejected')}
            id="filter-rejected"
          >
            {t('rejected')}
          </button>
        </div>
      </div>

      {/* Content Table / Empty state */}
      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '80px 0' }}>
          <div className="spinner spinner-primary" style={{ width: '30px', height: '30px' }} />
        </div>
      ) : error ? (
        <div className="alert alert-error">{error}</div>
      ) : requests.length === 0 ? (
        <div className="card empty-state animate-scale" style={{ background: '#fff' }}>
          <span className="emoji">📩</span>
          <h3>{t('noRequests')}</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '6px' }}>
            No access requests found with status "{statusFilter}"
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
                  <th>{t('tgUsername')}</th>
                  <th>{t('phone')}</th>
                  <th>Telegram ID</th>
                  <th>{t('joinedAt')}</th>
                  <th>{t('status')}</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((req) => (
                  <tr key={req.id}>
                    <td>{req.id}</td>
                    <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{req.full_name}</td>
                    <td>
                      {req.tg_username ? (
                        <a 
                          href={`https://t.me/${req.tg_username}`} 
                          target="_blank" 
                          rel="noreferrer"
                          style={{ color: 'var(--primary)', fontWeight: '500' }}
                        >
                          @{req.tg_username}
                        </a>
                      ) : '—'}
                    </td>
                    <td>{req.phone_number || '—'}</td>
                    <td style={{ fontFamily: 'monospace', fontSize: '13px' }}>{req.tg_user_id}</td>
                    <td style={{ fontSize: '13px' }}>{formatDate(req.created_at)}</td>
                    <td>
                      <span className={`badge ${getStatusBadgeClass(req.status)}`}>
                        {req.status === 'pending' && <Clock size={12} />}
                        {req.status === 'approved' && <UserCheck size={12} />}
                        {req.status === 'rejected' && <UserX size={12} />}
                        <span style={{ marginLeft: '4px' }}>{t(req.status)}</span>
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      {req.status === 'pending' && (
                        <div style={{ display: 'inline-flex', gap: '8px' }}>
                          <button 
                            className="btn btn-success btn-sm"
                            onClick={() => startApprovalFlow(req.id)}
                            style={{ padding: '6px 12px' }}
                            id={`approve-btn-${req.id}`}
                          >
                            <Check size={14} />
                            <span>{t('approve')}</span>
                          </button>
                          <button 
                            className="btn btn-danger btn-sm"
                            onClick={() => handleReject(req.id)}
                            style={{ padding: '6px 12px' }}
                            id={`reject-btn-${req.id}`}
                          >
                            <X size={14} />
                            <span>{t('reject')}</span>
                          </button>
                        </div>
                      )}
                      {req.status === 'approved' && req.password && (
                        <button 
                          className="btn btn-ghost btn-sm"
                          style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', border: '1px solid var(--border)' }}
                          onClick={() => setSelectedRequest({ id: req.id, password: req.password })}
                          id={`password-btn-${req.id}`}
                        >
                          <Copy size={13} />
                          <span>Show Credentials</span>
                        </button>
                      )}
                      {req.status !== 'pending' && !req.password && (
                        <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Reviewed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ===== ASSIGN LIMITS DIALOG MODAL ===== */}
      {assignModalOpen && (
        <div className="modal-overlay">
          <div className="modal animate-scale" style={{ maxWidth: '420px' }}>
            <h3 className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ClipboardCheck size={20} className="text-primary" />
              <span>{t('teacherLimits')}</span>
            </h3>
            
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
              Set resource limits for this teacher upon approval:
            </p>

            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label className="form-label" htmlFor="approval-max-tests">{t('maxTests')}</label>
              <input
                type="number"
                id="approval-max-tests"
                className="form-input"
                value={maxTests}
                onChange={(e) => setMaxTests(parseInt(e.target.value, 10))}
                min="1"
                style={{ width: '100%', padding: '10px 14px' }}
                required
              />
            </div>

            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label className="form-label" htmlFor="approval-max-students">{t('maxStudents')}</label>
              <input
                type="number"
                id="approval-max-students"
                className="form-input"
                value={maxStudents}
                onChange={(e) => setMaxStudents(parseInt(e.target.value, 10))}
                min="1"
                style={{ width: '100%', padding: '10px 14px' }}
                required
              />
            </div>

            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label className="form-label" htmlFor="approval-ai-limit">{t('aiQueriesLimit')}</label>
              <input
                type="number"
                id="approval-ai-limit"
                className="form-input"
                value={aiQueriesLimit}
                onChange={(e) => setAiQueriesLimit(parseInt(e.target.value, 10))}
                min="0"
                style={{ width: '100%', padding: '10px 14px' }}
                required
              />
            </div>

            <div className="form-group" style={{ marginBottom: '24px' }}>
              <label className="form-label" htmlFor="approval-expiry">{t('expiryDate')} (Optional)</label>
              <input
                type="date"
                id="approval-expiry"
                className="form-input"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
                style={{ width: '100%', padding: '10px 14px' }}
              />
            </div>


            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button 
                className="btn btn-ghost" 
                onClick={() => setAssignModalOpen(false)}
                id="cancel-assign-btn"
              >
                {t('cancel')}
              </button>
              <button 
                className="btn btn-primary" 
                onClick={handleApprove}
                id="confirm-assign-btn"
              >
                {t('approve')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ===== PASSWORD POPUP MODAL ===== */}
      {selectedRequest && (
        <div className="modal-overlay">
          <div className="modal animate-scale">
            <h3 className="modal-title">🔐 {t('tempPassword')}</h3>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
              The access request has been approved! Give this generated temporary credentials to the teacher to log in.
            </p>

            <div 
              style={{ 
                background: 'var(--bg-page)', 
                border: '1.5px solid var(--border)', 
                borderRadius: 'var(--radius-md)', 
                padding: '16px',
                marginBottom: '24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontFamily: 'monospace',
                fontSize: '18px',
                fontWeight: '700',
                letterSpacing: '1px',
                color: 'var(--text-primary)'
              }}
            >
              <span>{selectedRequest.password}</span>
              <button 
                className="btn btn-ghost btn-sm" 
                onClick={() => copyToClipboard(selectedRequest.password)}
                style={{ padding: '6px', borderRadius: 'var(--radius-sm)' }}
                title={t('copyPassword')}
                id="modal-copy-btn"
              >
                {copied ? <ClipboardCheck size={18} className="text-success" /> : <Copy size={18} />}
              </button>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button 
                className="btn btn-primary"
                onClick={() => setSelectedRequest(null)}
                style={{ padding: '10px 24px' }}
                id="modal-close-btn"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
