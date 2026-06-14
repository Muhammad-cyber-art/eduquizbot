import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../api';
import { Lock, User, Bot } from 'lucide-react';
import './Login.css';

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const { data } = await authAPI.login(username, password);
      localStorage.setItem('token', data.access_token);
      onLogin();
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-desktop">
      {/* macOS-style window */}
      <div className="login-window glass-heavy">
        {/* Traffic lights */}
        <div className="login-titlebar">
          <div className="traffic-lights">
            <button className="tl tl-red" />
            <button className="tl tl-yellow" />
            <button className="tl tl-green" />
          </div>
        </div>

        <div className="login-body">
          {/* App icon */}
          <div className="login-icon-wrap">
            <div className="login-icon">
              <Bot size={32} />
            </div>
          </div>

          <h1 className="login-title">EduQuiz Admin</h1>
          <p className="login-subtitle">Boshqaruv paneliga kirish</p>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="login-field">
              <User size={16} className="login-field-icon" />
              <input
                type="text"
                className="input login-input"
                placeholder="Login"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>

            <div className="login-field">
              <Lock size={16} className="login-field-icon" />
              <input
                type="password"
                className="input login-input"
                placeholder="Parol"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {error && <div className="login-error">{error}</div>}

            <button type="submit" className="btn btn-primary btn-login" disabled={loading}>
              {loading ? 'Kirilmoqda...' : 'Kirish'}
            </button>
          </form>

          <p className="login-hint">admin / admin123</p>
        </div>
      </div>
    </div>
  );
}
