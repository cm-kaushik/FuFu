import React, { useState, useRef } from 'react';
import { X } from 'lucide-react';
import { formatCurrency, displaySymbol } from '../utils/formatters';
import { buyStock, sellStock } from '../services/transactionApi';
import { getAIAdvice } from '../services/aiApi';
import { useAuth } from '../context/AuthContext';
import AIAdvisorPanel from './AIAdvisorPanel';

function BuySellModal({ stock, onClose, onSuccess }) {
  const { user, updateBalance } = useAuth();
  const [mode, setMode] = useState('buy'); // 'buy' or 'sell'
  const [quantity, setQuantity] = useState('');
  const [pin, setPin] = useState(['', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const pinRefs = [useRef(), useRef(), useRef(), useRef()];

  // AI Advisor state
  const [showAI, setShowAI] = useState(false);
  const [aiAdvice, setAiAdvice] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  const currentPrice = stock?.current_price || 0;
  const totalCost = currentPrice * (parseInt(quantity) || 0);

  const handlePinChange = (index, value) => {
    if (value.length > 1) return;
    const newPin = [...pin];
    newPin[index] = value;
    setPin(newPin);

    // Auto-focus next input
    if (value && index < 3) {
      pinRefs[index + 1].current?.focus();
    }
  };

  const handlePinKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !pin[index] && index > 0) {
      pinRefs[index - 1].current?.focus();
    }
  };

  const handleTrade = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const enteredPin = pin.join('');
    if (enteredPin.length !== 4) {
      setError('Please enter complete 4-digit PIN');
      return;
    }

    const qty = parseInt(quantity);
    if (!qty || qty <= 0) {
      setError('Please enter a valid quantity');
      return;
    }

    setLoading(true);

    try {
      const tradeFn = mode === 'buy' ? buyStock : sellStock;
      const res = await tradeFn(stock.symbol, qty, enteredPin);

      setSuccess(res.data.message);
      if (res.data.new_balance !== undefined) {
        updateBalance(res.data.new_balance);
      }

      setTimeout(() => {
        onSuccess?.();
        onClose();
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Trade failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchAIAdvice = async () => {
    setShowAI(true);
    setAiLoading(true);
    setAiAdvice(null);

    try {
      const res = await getAIAdvice({
        symbol: stock.symbol,
        action: mode.toUpperCase(),
        quantity: parseInt(quantity) || null,
        amount: totalCost || null,
      });
      setAiAdvice(res.data);
    } catch (err) {
      setAiAdvice({
        recommendation: 'N/A',
        sentiment: 'NEUTRAL',
        confidence: 0,
        reasoning: 'Failed to get AI advice. Please try again.',
        market_context: '',
        news_summary: '',
        risk_assessment: '',
        key_factors: [],
      });
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-with-ai" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{mode === 'buy' ? '📈' : '📉'} Trade {displaySymbol(stock?.symbol)}</h2>
          <button className="modal-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Buy/Sell Tabs */}
        <div className="modal-tabs">
          <button
            className={`modal-tab ${mode === 'buy' ? 'active buy' : ''}`}
            onClick={() => { setMode('buy'); setError(''); setSuccess(''); setShowAI(false); }}
          >
            Buy
          </button>
          <button
            className={`modal-tab ${mode === 'sell' ? 'active sell' : ''}`}
            onClick={() => { setMode('sell'); setError(''); setSuccess(''); setShowAI(false); }}
          >
            Sell
          </button>
        </div>

        {/* Stock Info */}
        <div className="modal-stock-info">
          <div className="stock-detail">
            <h3>{displaySymbol(stock?.symbol)}</h3>
            <p>{stock?.name}</p>
          </div>
          <div className="stock-price-info">
            <div className="price">{formatCurrency(currentPrice)}</div>
          </div>
        </div>

        {error && <div className="form-error">{error}</div>}
        {success && <div className="form-success">{success}</div>}

        <form onSubmit={handleTrade}>
          {/* Quantity */}
          <div className="form-group">
            <label>Quantity (Shares)</label>
            <input
              type="number"
              className="form-input"
              placeholder="Enter number of shares"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              min="1"
              required
            />
          </div>

          {/* Order Summary */}
          {quantity > 0 && (
            <div className="order-summary">
              <div className="summary-row">
                <span className="label">Price per share</span>
                <span className="value">{formatCurrency(currentPrice)}</span>
              </div>
              <div className="summary-row">
                <span className="label">Quantity</span>
                <span className="value">{quantity} shares</span>
              </div>
              <div className="summary-row total">
                <span className="label">Total {mode === 'buy' ? 'Cost' : 'Value'}</span>
                <span className="value">{formatCurrency(totalCost)}</span>
              </div>
              {mode === 'buy' && (
                <div className="summary-row">
                  <span className="label">Available Balance</span>
                  <span className="value">{formatCurrency(user?.balance || 0)}</span>
                </div>
              )}
            </div>
          )}

          {/* AI Advice Button */}
          <div style={{ marginBottom: '16px', textAlign: 'center' }}>
            <button
              type="button"
              className="btn-ai btn-sm"
              onClick={fetchAIAdvice}
              disabled={aiLoading}
            >
              🤖 {aiLoading ? 'Analyzing...' : 'Get AI Advice'}
            </button>
          </div>

          {/* AI Advisor Panel */}
          {showAI && (
            <AIAdvisorPanel
              advice={aiAdvice}
              loading={aiLoading}
              action={mode.toUpperCase()}
              onClose={() => setShowAI(false)}
            />
          )}

          {/* PIN Input */}
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
                  onChange={(e) => handlePinChange(idx, e.target.value)}
                  onKeyDown={(e) => handlePinKeyDown(idx, e)}
                  maxLength={1}
                />
              ))}
            </div>
          </div>

          {/* Trade Button */}
          <button
            type="submit"
            className={`btn-trade ${mode}`}
            disabled={loading || !quantity || pin.join('').length !== 4}
          >
            {loading
              ? 'Processing...'
              : `${mode === 'buy' ? 'Buy' : 'Sell'} ${quantity || 0} Shares`
            }
          </button>
        </form>
      </div>
    </div>
  );
}

export default BuySellModal;
