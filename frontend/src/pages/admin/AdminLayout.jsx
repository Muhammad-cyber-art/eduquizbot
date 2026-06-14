import { useState, useEffect } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { authAPI } from '../../api'
import { useLang } from '../../contexts/LangContext'
import { 
  LayoutDashboard, 
  ClipboardList, 
  Users, 
  BarChart2, 
  LogOut, 
  Globe,
  ChevronDown
} from 'lucide-react'

export default function AdminLayout() {
  const { lang, setLang, t } = useLang()
  const location = useLocation()
  const navigate = useNavigate()
  const [adminUser, setAdminUser] = useState('Admin')
  const [langOpen, setLangOpen] = useState(false)

  useEffect(() => {
    // Verify admin token and load profile details
    authAPI.me()
      .then(res => {
        if (res.data && res.data.username) {
          setAdminUser(res.data.username)
        }
      })
      .catch(() => {
        // Interceptor in api.js handles 401 auto-redirect
      })
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/admin/login')
  }

  const navItems = [
    { path: '/admin', label: t('dashboard'), icon: LayoutDashboard, exact: true },
    { path: '/admin/requests', label: t('requests'), icon: ClipboardList, exact: false },
    { path: '/admin/users', label: t('users'), icon: Users, exact: false },
    { path: '/admin/analytics', label: t('analytics'), icon: BarChart2, exact: false },
  ]

  const isActive = (item) => {
    if (item.exact) {
      return location.pathname === item.path
    }
    return location.pathname.startsWith(item.path) && location.pathname !== '/admin/login'
  }

  return (
    <div className="admin-layout animate-fade">
      {/* ===== SIDEBAR ===== */}
      <aside className="admin-sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon">📊</div>
          <div>
            <div className="logo-text">AlKhorazmiy</div>
            <div className="logo-sub">{t('adminTitle')}</div>
          </div>
        </div>

        {/* Sidebar Nav */}
        <nav className="sidebar-nav">
          {navItems.map((item, idx) => {
            const Icon = item.icon
            const active = isActive(item)
            return (
              <Link 
                key={idx} 
                to={item.path} 
                className={`sidebar-item ${active ? 'active' : ''}`}
                id={`nav-${item.path.split('/').pop() || 'dashboard'}`}
              >
                <Icon />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>

        {/* Language Switcher in Sidebar */}
        <div style={{ padding: '12px 20px', borderTop: '1px solid var(--border)' }}>
          <div className="lang-dropdown-container" style={{ width: '100%' }}>
            <button 
              className="lang-btn" 
              onClick={() => setLangOpen(!langOpen)} 
              style={{ width: '100%', justifyContent: 'space-between' }}
              id="sidebar-lang-btn"
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Globe size={15} />
                <span>{lang.toUpperCase()}</span>
              </span>
              <ChevronDown size={12} />
            </button>

            {langOpen && (
              <div className="lang-menu" style={{ width: '100%', bottom: '100%', top: 'auto', marginBottom: '8px' }}>
                <button 
                  className={`lang-item ${lang === 'uz' ? 'active' : ''}`}
                  onClick={() => { setLang('uz'); setLangOpen(false); }}
                >
                  Uzbekcha
                </button>
                <button 
                  className={`lang-item ${lang === 'ru' ? 'active' : ''}`}
                  onClick={() => { setLang('ru'); setLangOpen(false); }}
                >
                  Русский
                </button>
                <button 
                  className={`lang-item ${lang === 'en' ? 'active' : ''}`}
                  onClick={() => { setLang('en'); setLangOpen(false); }}
                >
                  English
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar Footer / User Section */}
        <div className="sidebar-footer">
          <div className="sidebar-avatar">
            👤
          </div>
          <div className="sidebar-username">
            {adminUser}
          </div>
          <button 
            onClick={handleLogout} 
            className="btn-ghost" 
            style={{ padding: '6px', borderRadius: '50%', color: 'var(--error)' }}
            title={t('logout')}
            id="logout-btn"
          >
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      {/* ===== SUBPAGE CONTENT ===== */}
      <main className="admin-content">
        <Outlet />
      </main>
    </div>
  )
}
