import React from 'react';
import { TrendingUp, TrendingDown, Wallet, BarChart3 } from 'lucide-react';
import { formatCurrency, formatPercent } from '../utils/formatters';

function PortfolioCard({ summary }) {
  if (!summary) return null;

  const isPnlPositive = summary.total_pnl >= 0;

  return (
    <div className="dashboard-stats">
      <div className="stat-card green">
        <div className="stat-icon"><Wallet size={22} /></div>
        <div className="stat-label">Balance</div>
        <div className="stat-value">{formatCurrency(summary.balance)}</div>
      </div>

      <div className="stat-card purple">
        <div className="stat-icon"><BarChart3 size={22} /></div>
        <div className="stat-label">Portfolio Value</div>
        <div className="stat-value">{formatCurrency(summary.portfolio_value)}</div>
      </div>

      <div className="stat-card blue">
        <div className="stat-icon"><TrendingUp size={22} /></div>
        <div className="stat-label">Total Invested</div>
        <div className="stat-value">{formatCurrency(summary.total_invested)}</div>
      </div>

      <div className={`stat-card ${isPnlPositive ? 'green' : 'orange'}`}>
        <div className="stat-icon">
          {isPnlPositive ? <TrendingUp size={22} /> : <TrendingDown size={22} />}
        </div>
        <div className="stat-label">Total P&L</div>
        <div className="stat-value">{formatCurrency(summary.total_pnl)}</div>
        <div className={`stat-change ${isPnlPositive ? 'positive' : 'negative'}`}>
          {formatPercent(summary.total_pnl_percent)}
        </div>
      </div>
    </div>
  );
}

export default PortfolioCard;
