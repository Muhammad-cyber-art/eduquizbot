import { useState, useEffect } from 'react';
import { usersAPI } from '../api';
import { Search, User } from 'lucide-react';
import './Users.css';

export default function Users() {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUsers();
  }, [roleFilter]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const params = {};
      if (roleFilter) params.role = roleFilter;
      if (search) params.search = search;
      const { data } = await usersAPI.list(params);
      setUsers(data);
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadUsers();
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleString('uz');
  };

  const getRoleBadge = (role) => {
    return `badge badge-${role.toLowerCase()}`;
  };

  return (
    <div className="users-page">
      <h1 className="page-title">Foydalanuvchilar</h1>

      <div className="users-controls">
        <div className="search-box">
          <Search size={18} />
          <input
            type="text"
            className="input"
            placeholder="Ism bo'yicha qidirish..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button className="btn btn-ghost" onClick={handleSearch}>
            Qidirish
          </button>
        </div>

        <div className="filter-tabs">
          <button
            className={`filter-tab ${roleFilter === '' ? 'active' : ''}`}
            onClick={() => setRoleFilter('')}
          >
            Barchasi
          </button>
          <button
            className={`filter-tab ${roleFilter === 'teacher' ? 'active' : ''}`}
            onClick={() => setRoleFilter('teacher')}
          >
            O'qituvchilar
          </button>
          <button
            className={`filter-tab ${roleFilter === 'student' ? 'active' : ''}`}
            onClick={() => setRoleFilter('student')}
          >
            Talabalar
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading-screen"><div className="loading-spinner"></div></div>
      ) : users.length === 0 ? (
        <div className="empty-state glass-card">
          <p>Foydalanuvchilar topilmadi</p>
        </div>
      ) : (
        <div className="glass-card table-card">
          <table className="glass-table">
            <thead>
              <tr>
                <th>Ism</th>
                <th>Telegram ID</th>
                <th>Rol</th>
                <th>Til</th>
                <th>Ro'yxatdan o'tgan</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>
                    <div className="user-cell">
                      <User size={16} />
                      {user.full_name || 'Noma\'lum'}
                    </div>
                  </td>
                  <td>
                    <a href={`tg://user?id=${user.tg_user_id}`} className="tg-link">
                      {user.tg_user_id}
                    </a>
                  </td>
                  <td>
                    <span className={getRoleBadge(user.role)}>
                      {user.role === 'teacher' ? 'O\'qituvchi' : 'Talaba'}
                    </span>
                  </td>
                  <td>{user.lang_code?.toUpperCase()}</td>
                  <td className="text-muted">{formatDate(user.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="users-count glass-card">
        Jami: <strong>{users.length}</strong> foydalanuvchi
      </div>
    </div>
  );
}
