import { useState, useEffect } from 'react';
import { requestsAPI } from '../api';
import { Check, X, Copy, User, Phone, AtSign } from 'lucide-react';
import './Requests.css';

export default function Requests() {
  const [requests, setRequests] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRequests();
  }, [filter]);

  const loadRequests = async () => {
    setLoading(true);
    try {
      const { data } = await requestsAPI.list(filter);
      setRequests(data);
    } catch (err) {
      console.error('Failed to load requests:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id) => {
    try {
      const { data } = await requestsAPI.approve(id);
      alert(`Parol yaratildi: ${data.password}\n\nBu parolni o'qituvchiga yuboring!`);
      loadRequests();
    } catch (err) {
      alert('Xatolik: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleReject = async (id) => {
    if (!confirm('Rostdan ham rad etasizmi?')) return;
    try {
      await requestsAPI.reject(id);
      loadRequests();
    } catch (err) {
      alert('Xatolik: ' + (err.response?.data?.detail || err.message));
    }
  };

  const copyPassword = (password) => {
    navigator.clipboard.writeText(password);
    alert('Parol nusxalandi!');
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: 'badge-pending',
      approved: 'badge-approved',
      rejected: 'badge-rejected',
      used: 'badge-used',
    };
    return `badge ${badges[status] || ''}`;
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString('uz');
  };

  return (
    <div className="requests-page">
      <h1 className="page-title">So'rovlar</h1>

      <div className="filter-tabs">
        {['all', 'pending', 'approved', 'rejected'].map((f) => (
          <button
            key={f}
            className={`filter-tab ${filter === f ? 'active' : ''}`}
            onClick={() => setFilter(f)}
          >
            {f === 'all' && 'Barchasi'}
            {f === 'pending' && 'Kutilmoqda'}
            {f === 'approved' && 'Tasdiqlangan'}
            {f === 'rejected' && 'Rad etilgan'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading-screen"><div className="loading-spinner"></div></div>
      ) : requests.length === 0 ? (
        <div className="empty-state glass-card">
          <p>So'rovlar topilmadi</p>
        </div>
      ) : (
        <div className="glass-card table-card">
          <table className="glass-table">
            <thead>
              <tr>
                <th>Ism</th>
                <th>Telegram</th>
                <th>Telefon</th>
                <th>Sana</th>
                <th>Status</th>
                <th>Parol</th>
                <th>Amallar</th>
              </tr>
            </thead>
            <tbody>
              {requests.map((req) => (
                <tr key={req.id}>
                  <td>
                    <div className="user-cell">
                      <User size={16} />
                      {req.full_name}
                    </div>
                  </td>
                  <td>
                    {req.tg_username ? (
                      <a href={`https://t.me/${req.tg_username}`} target="_blank" rel="noreferrer" className="tg-link">
                        <AtSign size={14} />
                        @{req.tg_username}
                      </a>
                    ) : (
                      <span className="text-muted">ID: {req.tg_user_id}</span>
                    )}
                  </td>
                  <td>
                    {req.phone_number ? (
                      <a href={`tel:${req.phone_number}`} className="phone-link">
                        <Phone size={14} />
                        {req.phone_number}
                      </a>
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                  <td className="text-muted">{formatDate(req.created_at)}</td>
                  <td>
                    <span className={getStatusBadge(req.status)}>
                      {req.status === 'pending' && 'Kutilmoqda'}
                      {req.status === 'approved' && 'Tasdiqlangan'}
                      {req.status === 'rejected' && 'Rad etilgan'}
                      {req.status === 'used' && 'Ishlatilgan'}
                    </span>
                  </td>
                  <td>
                    {req.password ? (
                      <div className="password-cell">
                        <code>{req.password}</code>
                        <button className="btn-icon" onClick={() => copyPassword(req.password)}>
                          <Copy size={14} />
                        </button>
                      </div>
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                  <td>
                    <div className="action-cell">
                      {req.status === 'pending' && (
                        <>
                          <button className="btn btn-success btn-sm" onClick={() => handleApprove(req.id)}>
                            <Check size={16} />
                          </button>
                          <button className="btn btn-danger btn-sm" onClick={() => handleReject(req.id)}>
                            <X size={16} />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
