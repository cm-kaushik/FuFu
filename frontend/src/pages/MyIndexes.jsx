import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, TrendingUp, Calendar, RefreshCw } from 'lucide-react';
import { getIndexes } from '../services/indexApi';
import IndexCard from '../components/IndexCard';

function MyIndexes() {
  const navigate = useNavigate();
  const [indexes, setIndexes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [nextRebalance, setNextRebalance] = useState('');
  const [rebalanceDue, setRebalanceDue] = useState(false);

  useEffect(() => {
    fetchIndexes();
  }, []);

  const fetchIndexes = async () => {
    try {
      const res = await getIndexes();
      setIndexes(res.data.indexes || []);
      setNextRebalance(res.data.next_rebalance || '');
      setRebalanceDue(res.data.rebalance_due || false);
    } catch (err) {
      console.error('Failed to fetch indexes:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen" style={{ height: '50vh', background: 'transparent' }}>
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>📊 My Custom Indexes</h1>
          <p>Your personalized indexes — like Nifty BeES, but built by you.</p>
        </div>
        <button className="btn-primary" onClick={() => navigate('/indexes/create')}>
          <Plus size={18} /> Create Index
        </button>
      </div>

      {/* Rebalance Notice */}
      <div className={`rebalance-notice ${rebalanceDue ? 'due' : ''}`}>
        <div className="rebalance-notice-content">
          <Calendar size={20} />
          <div>
            <strong>Next Rebalance:</strong> {nextRebalance}
            {rebalanceDue && (
              <span className="rebalance-badge">Rebalance Due!</span>
            )}
          </div>
        </div>
        <p className="text-muted" style={{ margin: '4px 0 0 28px', fontSize: '12px' }}>
          Follows Indian market convention — semi-annual rebalance in March & September
        </p>
      </div>

      {/* Stats Overview */}
      {indexes.length > 0 && (
        <div className="index-stats-row">
          <div className="index-stat-card">
            <span className="index-stat-label">Total Indexes</span>
            <span className="index-stat-value">{indexes.length}</span>
          </div>
          <div className="index-stat-card">
            <span className="index-stat-label">Total Invested</span>
            <span className="index-stat-value">
              ₹{indexes.reduce((sum, idx) => sum + (idx.total_invested || 0), 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="index-stat-card">
            <span className="index-stat-label">Portfolio Value</span>
            <span className="index-stat-value">
              ₹{indexes.reduce((sum, idx) => sum + (idx.current_value || 0), 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="index-stat-card">
            <span className="index-stat-label">Overall P&L</span>
            <span className={`index-stat-value ${
              indexes.reduce((sum, idx) => sum + (idx.pnl || 0), 0) >= 0 ? 'text-green' : 'text-red'
            }`}>
              ₹{indexes.reduce((sum, idx) => sum + (idx.pnl || 0), 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>
        </div>
      )}

      {/* Index Cards */}
      {indexes.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <h3>No Custom Indexes Yet</h3>
          <p>Create your first custom index to start tracking your personalized basket of stocks.</p>
          <button className="btn-primary" onClick={() => navigate('/indexes/create')}>
            <Plus size={18} /> Create Your First Index
          </button>
        </div>
      ) : (
        <div className="indexes-grid">
          {indexes.map(index => (
            <IndexCard
              key={index.id}
              index={index}
              onClick={() => navigate(`/indexes/${index.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default MyIndexes;
