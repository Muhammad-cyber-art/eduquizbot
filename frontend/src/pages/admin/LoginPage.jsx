import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authAPI } from '../../api'
import { useLang } from '../../contexts/LangContext'
import { User, Lock, ArrowLeft, LogIn } from 'lucide-react'

export default function LoginPage() {
  const { t } = useLang()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!username.trim() || !password.trim()) return

    setLoading(true)
    setError('')

    try {
      const response = await authAPI.login(username, password)
      const token = response.data.access_token
      localStorage.setItem('token', token)
      navigate('/admin')
    } catch (err) {
      console.error(err)
      setError(t('loginError'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div 
      className="animate-fade"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'var(--bg-page)',
        padding: '24px'
      }}
    >
      <div 
        className="card animate-scale"
        style={{
          width: '100%',
          maxWidth: '400px',
          padding: '36px',
          background: '#fff'
        }}
      >
        {/* Back Link */}
        <Link 
          to="/" 
          className="btn-ghost" 
          style={{ 
            display: 'inline-flex', 
            alignItems: 'center', 
            gap: '6px', 
            fontSize: '13px', 
            marginBottom: '24px',
            padding: '6px 12px',
            borderRadius: 'var(--radius-sm)'
          }}
        >
          <ArrowLeft size={14} />
          <span>{t('home')}</span>
        </Link>

        {/* Title */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div 
            style={{ 
              width: '48px', 
              height: '48px', 
              borderRadius: '12px', 
              background: 'linear-gradient(135deg, var(--primary), var(--primary-light))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '24px',
              margin: '0 auto 16px auto',
              boxShadow: 'var(--shadow-btn)'
            }}
          >
            📊
          </div>
          <h2 style={{ fontSize: '22px', fontWeight: '800' }}>{t('adminTitle')}</h2>
        </div>

        {/* Error Message */}
        {error && (
          <div className="alert alert-error animate-fade" style={{ marginBottom: '20px' }}>
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="form-group">
            <label className="form-label" htmlFor="username-input">{t('username')}</label>
            <div className="input-icon-wrap">
              <User className="input-icon" />
              <input
                id="username-input"
                type="text"
                className="form-input"
                placeholder={t('username')}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={loading}
                style={{ width: '100%' }}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password-input">{t('password')}</label>
            <div className="input-icon-wrap">
              <Lock className="input-icon" />
              <input
                id="password-input"
                type="password"
                className="form-input"
                placeholder={t('password')}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                style={{ width: '100%' }}
              />
            </div>
          </div>

          <button
            id="login-submit-btn"
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ 
              width: '100%', 
              justifyContent: 'center', 
              marginTop: '10px'
            }}
          >
            {loading ? (
              <div className="spinner" />
            ) : (
              <>
                <LogIn size={16} />
                <span>{t('login')}</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
