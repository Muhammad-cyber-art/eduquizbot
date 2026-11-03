import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, Mail, LogOut, Bot, Bell } from 'lucide-react';
import { useState } from 'react';
import './Layout.css';

export default function Layout({ onLogout }) {
  const navigate = useNavigate();
  const [time] = useState(() => {
    const now = new Date();
    return now.toLocaleTimeString('uz', { hour: '2-digit', minute: '2-digit' });
  });

  const handleLogout = () => {
    onLogout();
    navigate('/login');
  };

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/requests', icon: Mail, label: "So'rovlar" },
    { to: '/users', icon: Users, label: 'Foydalanuvchilar' },
  ];

  return (
    <div className="desktop">
      {/* macOS-style main window */}
      <div className="window glass-heavy">
        {/* Title bar */}
        <div className="titlebar">
          <div className="traffic-lights">
            <button className="tl tl-red" onClick={handleLogout} />
            <button className="tl tl-yellow" />
            <button className="tl tl-green" />
          </div>
          <div className="titlebar-center">
            <Bot size={16} className="titlebar-icon" />
            <span className="titlebar-text">EduQuiz Admin</span>
          </div>
          <div className="titlebar-right">
            <span className="titlebar-time">{time}</span>
            <button className="titlebar-btn">
              <Bell size={14} />
            </button>
          </div>
        </div>

        {/* Body: sidebar + content */}
        <div className="window-body">
          {/* Icon sidebar (macOS dock style) */}
          <nav className="dock">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) => `dock-item ${isActive ? 'active' : ''}`}
                title={label}
              >
                <div className="dock-icon">
                  <Icon size={18} />
                </div>
                <span className="dock-label">{label}</span>
              </NavLink>
            ))}

            <div className="dock-separator" />

            <button className="dock-item dock-logout" onClick={handleLogout} title="Chiqish">
              <div className="dock-icon">
                <LogOut size={18} />
              </div>
              <span className="dock-label">Chiqish</span>
            </button>
          </nav>

          {/* Main content area */}
          <main className="content-area">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
