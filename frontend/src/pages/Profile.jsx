import React from 'react';
import { useAuth } from '../context/AuthContext';
import { formatCurrency, formatDateTime } from '../utils/formatters';

function Profile() {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="profile-container">
      <div className="page-header">
        <h1>Profile</h1>
        <p>Manage your account details.</p>
      </div>

      <div className="profile-card">
        <div className="profile-avatar">
          {user.username.charAt(0).toUpperCase()}
        </div>
        
        <h2 style={{ fontSize: '1.5rem', marginBottom: '4px', color: 'var(--text-white)' }}>
          {user.username}
        </h2>
        <p style={{ color: 'var(--text-secondary)' }}>{user.email}</p>

        <div className="profile-info-grid">
          <div className="profile-info-item">
            <div className="info-label">Available Balance</div>
            <div className="info-value" style={{ color: 'var(--accent-primary)' }}>
              {formatCurrency(user.balance)}
            </div>
          </div>
          
          <div className="profile-info-item">
            <div className="info-label">Account Created</div>
            <div className="info-value">
              {user.created_at ? formatDateTime(user.created_at) : '—'}
            </div>
          </div>
          
          <div className="profile-info-item">
            <div className="info-label">Trade PIN</div>
            <div className="info-value" style={{ letterSpacing: '2px' }}>
              ****
            </div>
          </div>
        </div>

        <div style={{ marginTop: '36px', paddingTop: '24px', borderTop: '1px solid var(--border-color)' }}>
          <button 
            className="btn-primary" 
            style={{ 
              background: 'rgba(255, 107, 107, 0.1)', 
              color: 'var(--color-loss)',
              border: '1px solid rgba(255, 107, 107, 0.2)',
              width: 'auto',
              padding: '12px 32px'
            }}
            onClick={logout}
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}

export default Profile;
