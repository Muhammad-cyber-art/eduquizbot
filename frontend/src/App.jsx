import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/admin/LoginPage'
import AdminLayout from './pages/admin/AdminLayout'
import DashboardPage from './pages/admin/DashboardPage'
import RequestsPage from './pages/admin/RequestsPage'
import UsersPage from './pages/admin/UsersPage'
import AnalyticsPage from './pages/admin/AnalyticsPage'
import TeacherWebApp from './pages/webapp/TeacherWebApp'
import StudentWebApp from './pages/webapp/StudentWebApp'
import StartWebApp from './pages/webapp/StartWebApp'

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token')
  return token ? children : <Navigate to="/admin/login" replace />
}

export default function App() {
  const navigate = useNavigate()
  const [errorToast, setErrorToast] = useState(null)

  useEffect(() => {
    // 1. Listen for unauthorized events to securely logout and redirect
    const handleAuthError = () => {
      localStorage.removeItem('token')
      navigate('/admin/login', { replace: true })
    }

    // 2. Listen for generic API errors to show global notifications
    const handleApiError = (event) => {
      setErrorToast(event.detail || 'Noma\'lum server xatosi!')
      setTimeout(() => setErrorToast(null), 5000)
    }

    window.addEventListener('auth-unauthorized', handleAuthError)
    window.addEventListener('api-error', handleApiError)

    return () => {
      window.removeEventListener('auth-unauthorized', handleAuthError)
      window.removeEventListener('api-error', handleApiError)
    }
  }, [navigate])

  return (
    <>
      {errorToast && (
        <div style={{
          position: 'fixed', top: '20px', right: '20px', zIndex: 9999,
          background: '#ef4444', color: '#fff', padding: '12px 20px',
          borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          fontSize: '14px', fontWeight: 'bold', animation: 'slide-down 0.3s ease-out'
        }}>
          {errorToast}
        </div>
      )}
      <Routes>
      {/* Public landing */}
      <Route path="/" element={<LandingPage />} />

      {/* Admin auth */}
      <Route path="/admin/login" element={<LoginPage />} />

      {/* Admin panel */}
      <Route path="/admin" element={<ProtectedRoute><AdminLayout /></ProtectedRoute>}>
        <Route index element={<DashboardPage />} />
        <Route path="requests" element={<RequestsPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
      </Route>

      {/* Telegram WebApp Dashboards */}
      <Route path="/start" element={<StartWebApp />} />
      <Route path="/webapp/teacher" element={<TeacherWebApp />} />
      <Route path="/webapp/student" element={<StudentWebApp />} />
    </Routes>
    </>
  )
}

