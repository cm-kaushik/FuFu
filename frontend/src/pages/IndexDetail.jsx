import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, TrendingUp, TrendingDown, RefreshCw, Trash2, DollarSign, X } from 'lucide-react';
import { getIndexDetail, investInIndex, redeemFromIndex, rebalanceIndex, deleteIndex } from '../services/indexApi';
import { getAIAdvice } from '../services/aiApi';
import { formatCurrency } from '../utils/formatters';
import { useAuth } from '../context/AuthContext';
import AIAdvisorPanel from '../components/AIAdvisorPanel';
import WeightChart from '../components/WeightChart';
import NavChart from '../components/NavChart';

function IndexDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, updateBalance } = useAuth();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Invest/Redeem modals
  const [showInvestModal, setShowInvestModal] = useState(false);
  const [showRedeemModal, setShowRedeemModal] = useState(false);
  const [investAmount, setInvestAmount] = useState('');
  const [redeemAmount, setRedeemAmount] = useState('');
  const [redeemAll, setRedeemAll] = useState(false);
  const [pin, setPin] = useState(['', '', '', '']);
  const pinRefs = [useRef(), useRef(), useRef(), useRef()];
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState('');
  const [modalSuccess, setModalSuccess] = useState('');

  // AI Advisor
  const [showAI, setShowAI] = useState(false);
  const [aiAdvice, setAiAdvice] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiAction, setAiAction] = useState('BUY');

  useEffect(() => {
    fetchDetail();
  }, [id]);

  const fetchDetail = async () => {
    try {
      const res = await getIndexDetail(id);
      setData(res.data);
    } catch (err) {
      setError('Failed to load index details.');
    } finally {
      setLoading(false);
    }
  };

  const handlePinChange = (index, value) => {
    if (value.length > 1) return;
    const newPin = [...pin];
    newPin[index] = value;
    setPin(newPin);
    if (value && index < 3) pinRefs[index + 1].current?.focus();
  };

  const handlePinKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !pin[index] && index > 0) {
      pinRefs[index - 1].current?.focus();
    }
  };

  const resetModal = () => {
    setInvestAmount('');
    setRedeemAmount('');
    setRedeemAll(false);
    setPin(['', '', '', '']);
    setModalError('');
    setModalSuccess('');
    setModalLoading(false);
  };

  const handleInvest = async (e) => {
    e.preventDefault();
    setModalError('');
    setModalSuccess('');

    const enteredPin = pin.join('');
    if (enteredPin.length !== 4) { setModalError('Please enter complete 4-digit PIN'); return; }
    if (!investAmount || parseFloat(investAmount) <= 0) { setModalError('Enter a valid amount'); return; }

    setModalLoading(true);
    try {
      const res = await investInIndex(id, parseFloat(investAmount), enteredPin);
      setModalSuccess(res.data.message);
      if (res.data.new_balance !== undefined) updateBalance(res.data.new_balance);
      setTimeout(() => { setShowInvestModal(false); resetModal(); fetchDetail(); }, 1500);
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Investment failed.');
    } finally {
      setModalLoading(false);
    }
  };

  const handleRedeem = async (e) => {
    e.preventDefault();
    setModalError('');
    setModalSuccess('');

    const enteredPin = pin.join('');
    if (enteredPin.length !== 4) { setModalError('Please enter complete 4-digit PIN'); return; }
    if (!redeemAll && (!redeemAmount || parseFloat(redeemAmount) <= 0)) {
      setModalError('Enter a valid amount or select Redeem All');
      return;
    }

    setModalLoading(true);
    try {
      const res = await redeemFromIndex(id, redeemAll ? null : parseFloat(redeemAmount), enteredPin, redeemAll);
      setModalSuccess(res.data.message);
      if (res.data.new_balance !== undefined) updateBalance(res.data.new_balance);
      setTimeout(() => { setShowRedeemModal(false); resetModal(); fetchDetail(); }, 1500);
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Redemption failed.');
    } finally {
      setModalLoading(false);
    }
  };

  const handleRebalance = async () => {
    const enteredPin = prompt('Enter your 4-digit PIN to rebalance:');
    if (!enteredPin || enteredPin.length !== 4) return;

    try {
      const res = await rebalanceIndex(id, enteredPin);
      alert(res.data.message);
      fetchDetail();
    } catch (err) {
      alert(err.response?.data?.detail || 'Rebalance failed.');
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this index?')) return;
    try {
      await deleteIndex(id);
      navigate('/indexes');
    } catch (err) {
      alert(err.response?.data?.detail || 'Delete failed.');
    }
  };

  const fetchAIAdvice = async (action) => {
    setAiAction(action);
    setShowAI(true);
    setAiLoading(true);
    setAiAdvice(null);
    try {
      const res = await getAIAdvice({
        index_id: parseInt(id),
        action,
        amount: action === 'BUY' ? parseFloat(investAmount) || 10000 : parseFloat(redeemAmount) || null,
      });
      setAiAdvice(res.data);
    } catch (err) {
      setAiAdvice({ recommendation: 'N/A', sentiment: 'NEUTRAL', confidence: 0, reasoning: 'Failed to get AI advice.', market_context: '', news_summary: '', risk_assessment: '', key_factors: [] });
    } finally {
      setAiLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen" style={{ height: '50vh', background: 'transparent' }}>
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="empty-state">
        <h3>{error || 'Index not found'}</h3>
        <button className="btn-outline" onClick={() => navigate('/indexes')}>
          <ArrowLeft size={18} /> Back to Indexes
        </button>
      </div>
    );
  }

  const { index: idx, constituents, performance_history } = data;

  return (
    <div>
      {/* Header */}
      <div className="index-detail-header">
        <button className="btn-back" onClick={() => navigate('/indexes')}>
          <ArrowLeft size={18} /> Back
        </button>
        <div className="index-detail-title">
          <h1>{idx.name}</h1>
          <div className="index-detail-badges">
            {idx.theme && <span className="badge badge-theme">{idx.theme}</span>}
            {idx.sector && <span className="badge badge-sector">{idx.sector}</span>}
            <span className="badge badge-strategy">{idx.weight_strategy}</span>
          </div>
          {idx.description && <p className="text-muted">{idx.description}</p>}
        </div>
        <div className="index-detail-actions">
          <button className="btn-outline btn-sm" onClick={handleRebalance}>
            <RefreshCw size={16} /> Rebalance
          </button>
          <button className="btn-outline btn-sm btn-danger" onClick={handleDelete}>
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="index-detail-stats">
        <div className="stat-card">
          <span className="stat-label">NAV</span>
          <span className="stat-value">₹{idx.nav?.toFixed(2) || '100.00'}</span>
          <span className={`stat-change ${(idx.nav_change_percent || 0) >= 0 ? 'positive' : 'negative'}`}>
            {(idx.nav_change_percent || 0) >= 0 ? '+' : ''}{idx.nav_change_percent?.toFixed(2) || '0.00'}%
          </span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Invested</span>
          <span className="stat-value">{formatCurrency(idx.total_invested || 0)}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Current Value</span>
          <span className="stat-value">{formatCurrency(idx.current_value || 0)}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">P&L</span>
          <span className={`stat-value ${(idx.pnl || 0) >= 0 ? 'text-green' : 'text-red'}`}>
            {formatCurrency(idx.pnl || 0)}
          </span>
          <span className={`stat-change ${(idx.pnl_percent || 0) >= 0 ? 'positive' : 'negative'}`}>
            {(idx.pnl_percent || 0) >= 0 ? '+' : ''}{idx.pnl_percent?.toFixed(2) || '0.00'}%
          </span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Active Stocks</span>
          <span className="stat-value">{idx.active_stocks_count} / {idx.universe_size}</span>
          <span className="stat-change">Top {idx.top_n}</span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="index-action-buttons">
        <button className="btn-primary btn-invest" onClick={() => { resetModal(); setShowInvestModal(true); }}>
          <TrendingUp size={18} /> Invest
        </button>
        <button className="btn-outline btn-redeem" onClick={() => { resetModal(); setShowRedeemModal(true); }}>
          <TrendingDown size={18} /> Redeem
        </button>
        <button className="btn-ai" onClick={() => fetchAIAdvice('BUY')}>
          🤖 Get AI Advice
        </button>
      </div>

      {/* AI Advisor Panel */}
      {showAI && (
        <AIAdvisorPanel
          advice={aiAdvice}
          loading={aiLoading}
          action={aiAction}
          onClose={() => setShowAI(false)}
        />
      )}

      {/* Charts Row */}
      <div className="index-charts-row">
        <div className="chart-card">
          <h3>📈 NAV Performance</h3>
          <NavChart history={performance_history || []} />
        </div>
        <div className="chart-card">
          <h3>🥧 Weight Distribution</h3>
          <WeightChart
            constituents={constituents?.filter(c => c.is_active_in_index) || []}
          />
        </div>
      </div>

      {/* Constituents Table */}
      <div className="card" style={{ padding: '24px', marginTop: '16px' }}>
        <h3 style={{ marginBottom: '16px' }}>🏢 Constituents ({constituents?.length || 0} stocks)</h3>
        <div className="constituents-table">
          <div className="constituents-header">
            <span>Rank</span>
            <span>Stock</span>
            <span>Sector</span>
            <span>Price</span>
            <span>Change</span>
            <span>Weight</span>
            <span>Status</span>
          </div>
          {constituents?.map((c, idx) => (
            <div
              key={c.symbol}
              className={`constituent-row ${c.is_active_in_index ? 'active' : 'inactive'}`}
              onClick={() => navigate(`/stocks/${c.symbol}`)}
            >
              <span className="constituent-rank">#{c.rank_position}</span>
              <span className="constituent-symbol">
                <strong>{c.symbol.replace('.NS', '')}</strong>
                <small>{c.name}</small>
              </span>
              <span className="constituent-sector">{c.sector || '—'}</span>
              <span>{c.current_price ? formatCurrency(c.current_price) : '—'}</span>
              <span className={c.change_percent >= 0 ? 'text-green' : 'text-red'}>
                {c.change_percent != null ? `${c.change_percent >= 0 ? '+' : ''}${c.change_percent}%` : '—'}
              </span>
              <span>{c.weight_percent != null ? `${c.weight_percent.toFixed(1)}%` : '—'}</span>
              <span>
                {c.is_active_in_index ? (
                  <span className="badge badge-active">Active</span>
                ) : (
                  <span className="badge badge-inactive">Reserve</span>
                )}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Invest Modal */}
      {showInvestModal && (
        <div className="modal-overlay" onClick={() => { setShowInvestModal(false); resetModal(); }}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>📈 Invest in {idx.name}</h2>
              <button className="modal-close" onClick={() => { setShowInvestModal(false); resetModal(); }}>
                <X size={18} />
              </button>
            </div>

            <div className="modal-stock-info">
              <div>
                <p>Funds will be distributed across the Top {idx.top_n} stocks using <strong>{idx.weight_strategy}</strong> strategy.</p>
              </div>
            </div>

            {modalError && <div className="form-error">{modalError}</div>}
            {modalSuccess && <div className="form-success">{modalSuccess}</div>}

            <form onSubmit={handleInvest}>
              <div className="form-group">
                <label>Amount (₹)</label>
                <input
                  type="number"
                  className="form-input"
                  placeholder="Enter investment amount"
                  value={investAmount}
                  onChange={e => setInvestAmount(e.target.value)}
                  min="1"
                  required
                />
              </div>

              {investAmount > 0 && (
                <div className="order-summary">
                  <div className="summary-row">
                    <span className="label">Investment Amount</span>
                    <span className="value">{formatCurrency(parseFloat(investAmount))}</span>
                  </div>
                  <div className="summary-row">
                    <span className="label">Available Balance</span>
                    <span className="value">{formatCurrency(user?.balance || 0)}</span>
                  </div>
                </div>
              )}

              <div style={{ marginBottom: '16px', textAlign: 'center' }}>
                <button type="button" className="btn-ai btn-sm" onClick={() => fetchAIAdvice('BUY')}>
                  🤖 Get AI Advice Before Investing
                </button>
              </div>

              <div className="form-group">
                <label style={{ textAlign: 'center', display: 'block' }}>Enter PIN to confirm</label>
                <div className="pin-input-group">
                  {pin.map((digit, idx) => (
                    <input
                      key={idx}
                      ref={pinRefs[idx]}
                      type="password"
                      className="pin-digit"
                      value={digit}
                      onChange={e => handlePinChange(idx, e.target.value)}
                      onKeyDown={e => handlePinKeyDown(idx, e)}
                      maxLength={1}
                    />
                  ))}
                </div>
              </div>

              <button type="submit" className="btn-trade buy" disabled={modalLoading || !investAmount || pin.join('').length !== 4}>
                {modalLoading ? 'Processing...' : `Invest ₹${investAmount || 0}`}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Redeem Modal */}
      {showRedeemModal && (
        <div className="modal-overlay" onClick={() => { setShowRedeemModal(false); resetModal(); }}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>📉 Redeem from {idx.name}</h2>
              <button className="modal-close" onClick={() => { setShowRedeemModal(false); resetModal(); }}>
                <X size={18} />
              </button>
            </div>

            {modalError && <div className="form-error">{modalError}</div>}
            {modalSuccess && <div className="form-success">{modalSuccess}</div>}

            <form onSubmit={handleRedeem}>
              <div className="form-group">
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input
                    type="checkbox"
                    checked={redeemAll}
                    onChange={e => setRedeemAll(e.target.checked)}
                  />
                  Redeem All
                </label>
              </div>

              {!redeemAll && (
                <div className="form-group">
                  <label>Amount (₹)</label>
                  <input
                    type="number"
                    className="form-input"
                    placeholder="Enter redeem amount"
                    value={redeemAmount}
                    onChange={e => setRedeemAmount(e.target.value)}
                    min="1"
                  />
                </div>
              )}

              <div className="order-summary">
                <div className="summary-row">
                  <span className="label">Current Value</span>
                  <span className="value">{formatCurrency(idx.current_value || 0)}</span>
                </div>
              </div>

              <div style={{ marginBottom: '16px', textAlign: 'center' }}>
                <button type="button" className="btn-ai btn-sm" onClick={() => fetchAIAdvice('SELL')}>
                  🤖 Get AI Advice Before Redeeming
                </button>
              </div>

              <div className="form-group">
                <label style={{ textAlign: 'center', display: 'block' }}>Enter PIN to confirm</label>
                <div className="pin-input-group">
                  {pin.map((digit, idx) => (
                    <input
                      key={idx}
                      ref={pinRefs[idx]}
                      type="password"
                      className="pin-digit"
                      value={digit}
                      onChange={e => handlePinChange(idx, e.target.value)}
                      onKeyDown={e => handlePinKeyDown(idx, e)}
                      maxLength={1}
                    />
                  ))}
                </div>
              </div>

              <button type="submit" className="btn-trade sell" disabled={modalLoading || pin.join('').length !== 4}>
                {modalLoading ? 'Processing...' : 'Confirm Redemption'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default IndexDetail;
