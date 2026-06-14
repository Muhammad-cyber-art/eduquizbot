import { useState, useEffect, useCallback } from 'react'
import { analyticsAPI } from '../../api'
import { useLang } from '../../contexts/LangContext'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'
import { BarChart2, RefreshCw, Calendar, TrendingUp, Activity } from 'lucide-react'

export default function AnalyticsPage() {
  const { t } = useLang()
  const [days, setDays] = useState(30)
  const [growthData, setGrowthData] = useState([])
  const [activityData, setActivityData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchAnalytics = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [growthRes, activityRes] = await Promise.all([
        analyticsAPI.userGrowth(days),
        analyticsAPI.activity(days)
      ])
      setGrowthData(growthRes.data)
      setActivityData(activityRes.data)
    } catch (err) {
      console.error(err)
      setError('Failed to fetch analytics data.')
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    fetchAnalytics()
  }, [days, fetchAnalytics])

  // Helper to format chart dates to simpler format
  const formatChartDate = (dateStr) => {
    try {
      const d = new Date(dateStr)
      if (isNaN(d.getTime())) return dateStr
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
    } catch {
      return dateStr
    }
  }

  // Custom tooltips for nice hover card styling
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div 
          style={{ 
            background: '#fff', 
            border: '1.5px solid var(--border)', 
            padding: '12px 16px', 
            borderRadius: 'var(--radius-md)',
            boxShadow: 'var(--shadow-elevated)'
          }}
        >
          <p style={{ fontWeight: '700', fontSize: '13px', color: 'var(--text-primary)', marginBottom: '4px' }}>
            {formatChartDate(label)}
          </p>
          <p style={{ fontSize: '14px', color: payload[0].stroke, fontWeight: '600' }}>
            {payload[0].name}: <span style={{ fontWeight: '800' }}>{payload[0].value}</span>
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="admin-page animate-fade">
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">{t('analyticsTitle')}</h1>
          <p className="page-sub">{t('analyticsSub')}</p>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {/* Days selector */}
          <div className="filter-chips">
            <button 
              className={`chip ${days === 7 ? 'active' : ''}`}
              onClick={() => setDays(7)}
              id="days-7-btn"
            >
              {t('days7')}
            </button>
            <button 
              className={`chip ${days === 30 ? 'active' : ''}`}
              onClick={() => setDays(30)}
              id="days-30-btn"
            >
              {t('days30')}
            </button>
          </div>

          <button 
            className="btn btn-ghost" 
            onClick={fetchAnalytics}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', border: '1px solid var(--border)', padding: '10px 14px' }}
            id="refresh-analytics-btn"
          >
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {/* Main Charts */}
      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '120px 0' }}>
          <div className="spinner spinner-primary" style={{ width: '40px', height: '40px' }} />
        </div>
      ) : error ? (
        <div className="alert alert-error">{error}</div>
      ) : (
        <div 
          style={{ 
            display: 'grid', 
            gridTemplateColumns: '1fr', 
            gap: '32px',
            marginTop: '16px' 
          }}
          className="animate-fade-up"
        >
          {/* User Growth Chart */}
          <div className="card" style={{ padding: '28px', background: '#fff' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '800', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <TrendingUp size={20} className="text-primary" />
              <span>{t('userGrowthChart')}</span>
            </h3>

            <div style={{ width: '100%', height: '320px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={growthData} margin={{ top: 10, right: 20, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--divider)" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={formatChartDate} 
                    stroke="var(--text-muted)" 
                    fontSize={11} 
                    fontWeight={600}
                  />
                  <YAxis 
                    stroke="var(--text-muted)" 
                    fontSize={11} 
                    fontWeight={600}
                    allowDecimals={false}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Line 
                    name="Registrations"
                    type="monotone" 
                    dataKey="count" 
                    stroke="var(--primary)" 
                    strokeWidth={3} 
                    activeDot={{ r: 6 }} 
                    dot={{ strokeWidth: 2, r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Activity Chart */}
          <div className="card" style={{ padding: '28px', background: '#fff' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '800', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Activity size={20} style={{ color: '#8E59B6' }} />
              <span>{t('activityChart')}</span>
            </h3>

            <div style={{ width: '100%', height: '320px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={activityData} margin={{ top: 10, right: 20, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--divider)" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={formatChartDate} 
                    stroke="var(--text-muted)" 
                    fontSize={11} 
                    fontWeight={600}
                  />
                  <YAxis 
                    stroke="var(--text-muted)" 
                    fontSize={11} 
                    fontWeight={600}
                    allowDecimals={false}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Line 
                    name="Attempts Taken"
                    type="monotone" 
                    dataKey="count" 
                    stroke="#8E59B6" 
                    strokeWidth={3} 
                    activeDot={{ r: 6 }} 
                    dot={{ strokeWidth: 2, r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
