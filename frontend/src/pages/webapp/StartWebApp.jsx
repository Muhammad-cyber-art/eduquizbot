import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

export default function StartWebApp() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const controller = new AbortController()
    const fetchUserRole = async () => {
      const tgUser = window.Telegram?.WebApp?.initDataUnsafe?.user
      const tgUserId = tgUser?.id || localStorage.getItem('dev_student_tg_id') || '8935558785'

      try {
        const res = await axios.get('/api/webapp/user/role', {
          headers: { 'X-TG-Init-Data': window.Telegram?.WebApp?.initData || `DEV_${tgUserId}` },
          signal: controller.signal
        })
        const role = res.data.role
        if (role === 'teacher') {
          navigate('/webapp/teacher', { replace: true })
        } else if (role === 'student') {
          navigate('/webapp/student', { replace: true })
        } else {
          setError("Siz tizimdan ro'yxatdan o'tmagansiz. Iltimos, Telegram bot orqali qayta urining.")
        }
      } catch (err) {
        if (axios.isCancel(err)) return
        console.error(err)
        setError("Foydalanuvchi ma'lumotlarini aniqlashda xatolik yuz berdi.")
      } finally {
        setLoading(false)
      }
    }

    fetchUserRole()
    return () => controller.abort()
  }, [navigate])

  if (loading) {
    return (
      <div className="glass-bg" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <div className="spinner spinner-primary" style={{ width: '36px', height: '36px', borderWidth: '3px' }} />
        <p style={{ marginTop: '12px', color: 'var(--text-secondary)', fontSize: '14px', fontWeight: '500' }}>Aniqlanmoqda...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass-bg" style={{ padding: '20px', minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <div className="glass-card" style={{ padding: '32px 24px', textAlign: 'center' }}>
          <div style={{ color: 'var(--error)', fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
          <h3 style={{ color: 'var(--text-primary)', marginBottom: '8px', fontSize: '20px', fontWeight: '800' }}>Xatolik</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>{error}</p>
        </div>
      </div>
    )
  }

  return null
}
