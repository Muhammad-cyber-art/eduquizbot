import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useLang } from '../contexts/LangContext'
import {
  MessageSquare,
  Award,
  Clock,
  ArrowRight,
  Globe,
  ChevronDown,
  BookOpen,
  Users,
  CheckCircle,
  BarChart2,
  FileText,
  Smartphone,
  Check,
  Send,
  Zap
} from 'lucide-react'
import './LandingPage.css'

export default function LandingPage() {
  const { lang, setLang, t } = useLang()
  const [scrolled, setScrolled] = useState(false)
  const [langMenuOpen, setLangMenuOpen] = useState(false)

  // Listen to scroll events to toggle glassmorphism shadow
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        setScrolled(true)
      } else {
        setScrolled(false)
      }
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div className="landing-layout">
      {/* ===== HEADER / NAVBAR ===== */}
      <nav className={`navbar-container ${scrolled ? 'scrolled' : ''}`}>
        <div className="container navbar-inner">
          <div className="nav-logo">
            <div className="logo-icon">📊</div>
            <span>AlKhorazmiyQuiz</span>
          </div>

          <div className="nav-links">
            <a href="#features" className="nav-link">{t('features')}</a>
            <a href="#how" className="nav-link">{t('howItWorks')}</a>
            <a href="#register" className="nav-link">{t('register')}</a>
          </div>

          <div className="nav-actions">
            {/* Language Switcher */}
            <div className="lang-dropdown-container">
              <button 
                className="lang-btn" 
                onClick={() => setLangMenuOpen(!langMenuOpen)}
                id="lang-selector-btn"
              >
                <Globe size={16} />
                <span>{lang.toUpperCase()}</span>
                <ChevronDown size={14} />
              </button>

              {langMenuOpen && (
                <div className="lang-menu">
                  <button 
                    className={`lang-item ${lang === 'uz' ? 'active' : ''}`}
                    onClick={() => { setLang('uz'); setLangMenuOpen(false); }}
                  >
                    Uzbekcha
                  </button>
                  <button 
                    className={`lang-item ${lang === 'ru' ? 'active' : ''}`}
                    onClick={() => { setLang('ru'); setLangMenuOpen(false); }}
                  >
                    Русский
                  </button>
                  <button 
                    className={`lang-item ${lang === 'en' ? 'active' : ''}`}
                    onClick={() => { setLang('en'); setLangMenuOpen(false); }}
                  >
                    English
                  </button>
                </div>
              )}
            </div>


          </div>
        </div>
      </nav>

      {/* ===== HERO SECTION ===== */}
      <header className="hero-section">
        <div className="container hero-grid">
          <div className="hero-content animate-fade-up">
            <div className="hero-badge">
              <Zap size={14} className="text-accent" />
              <span>@alkhorazmiy_bot</span>
            </div>
            <h1 className="hero-title">{t('heroTitle')}</h1>
            <p className="hero-subtitle">{t('heroSubtitle')}</p>
            
            <div className="hero-actions">
              <a 
                href="https://t.me/alkhorazmiy_bot" 
                target="_blank" 
                rel="noreferrer" 
                className="btn btn-accent"
                id="hero-start-bot-btn"
              >
                {t('openBot')}
                <ArrowRight size={18} />
              </a>

            </div>

            <div className="hero-stats">
              <div className="hero-stat-item">
                <span className="hero-stat-val">150+</span>
                <span className="hero-stat-lbl">{t('statsTeachers')}</span>
              </div>
              <div className="hero-stat-item">
                <span className="hero-stat-val">2,400+</span>
                <span className="hero-stat-lbl">{t('statsQuizzes')}</span>
              </div>
              <div className="hero-stat-item">
                <span className="hero-stat-val">50,000+</span>
                <span className="hero-stat-lbl">{t('statsAttempts')}</span>
              </div>
            </div>
          </div>

          <div className="hero-graphic animate-scale">
            <div className="bot-mockup">
              <div className="bot-header">
                <div className="bot-avatar">🤖</div>
                <div className="bot-info">
                  <span className="bot-name">AlKhorazmiyQuiz Bot</span>
                  <span className="bot-status">bot</span>
                </div>
              </div>
              <div className="bot-messages">
                <div className="msg msg-bot">
                  👋 <b>Xush kelibsiz!</b> AlKhorazmiyQuiz test tizimi botiga xush kelibsiz.
                  <span className="msg-time">12:00</span>
                </div>
                <div className="msg msg-bot">
                  👤 Rolingizni tanlang:
                  <span className="msg-time">12:00</span>
                </div>
                <div className="msg msg-user">
                  👨‍🏫 O'qituvchi
                  <span className="msg-time">12:01</span>
                </div>
                <div className="msg msg-bot">
                  📝 Test nomini kiriting:
                  <span className="msg-time">12:01</span>
                </div>
                <div className="msg msg-user">
                  Olimpiada Matematika 2026
                  <span className="msg-time">12:01</span>
                </div>
                <div className="msg msg-bot">
                  📎 Savollar faylini yuboring (.docx / .pdf / .txt):
                  <span className="msg-time">12:02</span>
                </div>
                <div className="msg msg-user">
                  📄 matematika_savollar.docx
                  <span className="msg-time">12:02</span>
                </div>
                <div className="msg msg-bot">
                  ✅ <b>Test muvaffaqiyatli yaratildi!</b><br />
                  Savollar soni: 20 ta<br />
                  Test ID: <b>74921</b><br /><br />
                  Ushbu ID-ni o'quvchilaringizga ulashing.
                  <span className="msg-time">12:02</span>
                </div>
              </div>
              <div className="bot-keyboard">
                <div className="kb-btn kb-btn-accent">📊 Test hisobotini Excelda yuklash</div>
                <div className="kb-btn">⚙️ Sozlamalar</div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* ===== FEATURES SECTION ===== */}
      <section id="features" className="section bg-page">
        <div className="container text-center">
          <div style={{ maxWidth: '640px', margin: '0 auto 56px auto', textAlign: 'center' }}>
            <h2 style={{ fontSize: '32px', fontWeight: '800', marginBottom: '16px' }}>{t('featTitle')}</h2>
            <p className="text-secondary">{t('featSub')}</p>
          </div>

          <div className="features-grid">
            <div className="feature-card">
              <div className="feat-icon-box">
                <FileText size={24} />
              </div>
              <h3>{t('feat1Title')}</h3>
              <p>{t('feat1Desc')}</p>
            </div>

            <div className="feature-card">
              <div className="feat-icon-box">
                <CheckCircle size={24} />
              </div>
              <h3>{t('feat2Title')}</h3>
              <p>{t('feat2Desc')}</p>
            </div>

            <div className="feature-card">
              <div className="feat-icon-box">
                <BarChart2 size={24} />
              </div>
              <h3>{t('feat3Title')}</h3>
              <p>{t('feat3Desc')}</p>
            </div>

            <div className="feature-card">
              <div className="feat-icon-box">
                <Clock size={24} />
              </div>
              <h3>{t('feat4Title')}</h3>
              <p>{t('feat4Desc')}</p>
            </div>

            <div className="feature-card">
              <div className="feat-icon-box">
                <Smartphone size={24} />
              </div>
              <h3>{t('feat5Title')}</h3>
              <p>{t('feat5Desc')}</p>
            </div>

            <div className="feature-card">
              <div className="feat-icon-box">
                <Users size={24} />
              </div>
              <h3>{t('feat6Title')}</h3>
              <p>{t('feat6Desc')}</p>
            </div>
          </div>
        </div>
      </section>

      {/* ===== HOW IT WORKS SECTION ===== */}
      <section id="how" className="section" style={{ background: '#fff' }}>
        <div className="container">
          <div style={{ maxWidth: '640px', margin: '0 auto 56px auto', textAlign: 'center' }}>
            <h2 style={{ fontSize: '32px', fontWeight: '800', marginBottom: '16px' }}>{t('howTitle')}</h2>
            <p className="text-secondary">{t('howSub')}</p>
          </div>

          <div className="how-steps">
            <div className="step-card">
              <div className="step-number-circle">1</div>
              <h3>{t('step1Title')}</h3>
              <p>{t('step1Desc')}</p>
            </div>

            <div className="step-card">
              <div className="step-number-circle">2</div>
              <h3>{t('step2Title')}</h3>
              <p>{t('step2Desc')}</p>
            </div>

            <div className="step-card">
              <div className="step-number-circle">3</div>
              <h3>{t('step3Title')}</h3>
              <p>{t('step3Desc')}</p>
            </div>
          </div>
        </div>
      </section>

      {/* ===== REGISTRATION / CTA SECTION ===== */}
      <section id="register" className="section reg-section bg-page">
        <div className="container">
          <div className="reg-card">
            <div className="reg-info">
              <h2>{t('regTitle')}</h2>
              <p>{t('regSub')}</p>

              <div className="reg-list">
                <div className="reg-item">
                  <div className="reg-check"><Check size={12} /></div>
                  <span className="reg-item-text">{t('regStep1')}</span>
                </div>
                <div className="reg-item">
                  <div className="reg-check"><Check size={12} /></div>
                  <span className="reg-item-text">{t('regStep2')}</span>
                </div>
                <div className="reg-item">
                  <div className="reg-check"><Check size={12} /></div>
                  <span className="reg-item-text">{t('regStep3')}</span>
                </div>
                <div className="reg-item">
                  <div className="reg-check"><Check size={12} /></div>
                  <span className="reg-item-text">{t('regStep4')}</span>
                </div>
                <div className="reg-item">
                  <div className="reg-check"><Check size={12} /></div>
                  <span className="reg-item-text">{t('regStep5')}</span>
                </div>
              </div>
            </div>

            <div className="reg-cta-box">
              <div className="reg-qr">
                <div className="reg-qr-placeholder">
                  🤖<br />
                  Scan to start bot in Telegram
                </div>
              </div>
              <a 
                href="https://t.me/alkhorazmiy_bot" 
                target="_blank" 
                rel="noreferrer" 
                className="btn btn-primary"
                style={{ width: '100%', justifyContent: 'center' }}
                id="register-bot-link"
              >
                {t('regCTA')}
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <footer className="landing-footer">
        <div className="container">
          <div className="footer-inner">
            <div className="footer-logo">
              <span>📊 AlKhorazmiyQuiz</span>
            </div>
            <div className="footer-links">
              <a href="#features" className="footer-link">{t('features')}</a>
              <a href="#how" className="footer-link">{t('howItWorks')}</a>
              <a href="https://t.me/alkhorazmiy_bot" target="_blank" rel="noreferrer" className="footer-link">@alkhorazmiy_bot</a>
            </div>
          </div>
          <div className="footer-copy">
            <p>&copy; {new Date().getFullYear()} AlKhorazmiyQuiz. {t('footerRights')}</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
