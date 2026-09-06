import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, TrendingUp, TrendingDown } from 'lucide-react';
import useStock from '../hooks/useStock';
import PriceChart from '../components/PriceChart';
import BuySellModal from '../components/BuySellModal';
import { formatCurrency, formatLargeNumber, displaySymbol } from '../utils/formatters';

function StockDetails() {
  const { symbol } = useParams();
  const navigate = useNavigate();
  const { stock, history, loading, error, period, setPeriod } = useStock(symbol);
  const [showModal, setShowModal] = useState(false);

  if (loading && !stock) {
    return (
      <div className="loading-screen" style={{ height: '70vh', background: 'transparent' }}>
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state">
        <h3>Error loading stock details</h3>
        <p>{error}</p>
        <button className="btn-primary" style={{ width: 'auto', marginTop: '16px' }} onClick={() => navigate('/stocks')}>
          Back to Stocks
        </button>
      </div>
    );
  }

  if (!stock) return null;

  const isPositive = (stock.change || 0) >= 0;

  return (
    <div>
      <button 
        onClick={() => navigate('/stocks')}
        style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'none', color: 'var(--text-secondary)', marginBottom: '20px', fontSize: '0.9rem', fontWeight: 600 }}
      >
        <ArrowLeft size={16} /> Back to Market
      </button>

      <div className="stock-detail-header">
        <div className="stock-detail-info">
          <h1>{stock.name}</h1>
          <div className="symbol-badge">{displaySymbol(stock.symbol)} • {stock.exchange}</div>
          {stock.sector && <div style={{ marginTop: '8px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>{stock.sector}</div>}
        </div>

        <div className="stock-detail-price">
          <div className="price">{formatCurrency(stock.current_price)}</div>
          <div className={`change-info ${isPositive ? 'positive' : 'negative'}`}>
            {isPositive ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
            {isPositive ? '+' : ''}{stock.change?.toFixed(2)} ({isPositive ? '+' : ''}{stock.change_percent?.toFixed(2)}%)
          </div>
          <div className="stock-detail-actions">
            <button className="btn-buy" onClick={() => setShowModal(true)}>BUY</button>
            <button className="btn-sell" onClick={() => setShowModal(true)}>SELL</button>
          </div>
        </div>
      </div>

      <div className="stock-metrics">
        <div className="metric-card">
          <div className="metric-label">Open</div>
          <div className="metric-value">{formatCurrency(stock.open_price)}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Previous Close</div>
          <div className="metric-value">{formatCurrency(stock.previous_close)}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Day High</div>
          <div className="metric-value">{formatCurrency(stock.day_high)}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Day Low</div>
          <div className="metric-value">{formatCurrency(stock.day_low)}</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-label">Volume</div>
          <div className="metric-value">{new Intl.NumberFormat('en-IN').format(stock.volume || 0)}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Market Cap</div>
          <div className="metric-value">{formatLargeNumber(stock.market_cap)}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">52W High</div>
          <div className="metric-value">{formatCurrency(stock.fifty_two_week_high)}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">52W Low</div>
          <div className="metric-value">{formatCurrency(stock.fifty_two_week_low)}</div>
        </div>
      </div>

      <PriceChart 
        data={history} 
        period={period} 
        onPeriodChange={setPeriod} 
        title={`${displaySymbol(stock.symbol)} Price History`}
      />

      {showModal && (
        <BuySellModal 
          stock={stock} 
          onClose={() => setShowModal(false)}
          onSuccess={() => {
            // Optional: refresh portfolio data if needed
          }}
        />
      )}
    </div>
  );
}

export default StockDetails;
