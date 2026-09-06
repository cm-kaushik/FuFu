import React from 'react';
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';

function IndexCard({ index, onClick }) {
  const pnl = index.pnl || 0;
  const pnlPercent = index.pnl_percent || 0;
  const isPositive = pnl >= 0;

  return (
    <div className="index-card" onClick={onClick}>
      <div className="index-card-header">
        <div className="index-card-title">
          <h3>{index.name}</h3>
          <div className="index-card-badges">
            {index.theme && <span className="badge badge-theme">{index.theme}</span>}
            <span className="badge badge-strategy">{index.weight_strategy}</span>
          </div>
        </div>
        <div className={`index-card-nav ${isPositive ? 'positive' : 'negative'}`}>
          <span className="nav-value">₹{(index.nav || 100).toFixed(2)}</span>
          <span className="nav-change">
            {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            {isPositive ? '+' : ''}{(index.nav_change_percent || 0).toFixed(2)}%
          </span>
        </div>
      </div>

      <div className="index-card-meta">
        <span>Top {index.top_n} of {index.universe_size}</span>
        <span>•</span>
        <span>{index.active_stocks_count} active</span>
        {index.sector && (
          <>
            <span>•</span>
            <span>{index.sector}</span>
          </>
        )}
      </div>

      {index.total_invested > 0 ? (
        <div className="index-card-investment">
          <div className="index-card-inv-row">
            <span>Invested</span>
            <span>₹{index.total_invested.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
          </div>
          <div className="index-card-inv-row">
            <span>Current</span>
            <span>₹{index.current_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
          </div>
          <div className={`index-card-inv-row pnl ${isPositive ? 'positive' : 'negative'}`}>
            <span>P&L</span>
            <span>
              {isPositive ? '+' : ''}₹{pnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              {' '}({isPositive ? '+' : ''}{pnlPercent.toFixed(2)}%)
            </span>
          </div>
        </div>
      ) : (
        <div className="index-card-no-invest">
          <BarChart3 size={16} />
          <span>Not yet invested</span>
        </div>
      )}

      <div className="index-card-footer">
        <span className="index-card-rebalance">🔄 Semi-Annual (Mar/Sep)</span>
        <span className="index-card-arrow">→</span>
      </div>
    </div>
  );
}

export default IndexCard;
