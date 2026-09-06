import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Briefcase, TrendingUp, TrendingDown } from 'lucide-react';
import { getPortfolio } from '../services/portfolioApi';
import PortfolioCard from '../components/PortfolioCard';
import { formatCurrency, formatPercent, displaySymbol } from '../utils/formatters';

function Portfolio() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPortfolio()
      .then((res) => setData(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="loading-screen" style={{ height: '50vh', background: 'transparent' }}>
        <div className="loading-spinner"></div>
      </div>
    );
  }

  const { summary, holdings } = data || {};

  return (
    <div>
      <div className="page-header">
        <h1>Your Portfolio</h1>
        <p>Manage your holdings and track performance.</p>
      </div>

      <PortfolioCard summary={summary} />

      <div className="dashboard-section-title" style={{ marginTop: '32px' }}>
        Current Holdings ({holdings?.length || 0})
      </div>

      {holdings && holdings.length > 0 ? (
        <div className="portfolio-grid">
          {holdings.map((holding) => {
            const isPositive = holding.pnl >= 0;
            return (
              <div 
                key={holding.stock_symbol} 
                className="portfolio-holding-card"
                onClick={() => navigate(`/stocks/${holding.stock_symbol}`)}
                style={{ cursor: 'pointer' }}
              >
                <div className="holding-header">
                  <div>
                    <div className="symbol">{displaySymbol(holding.stock_symbol)}</div>
                    <div className="name">{holding.stock_name}</div>
                  </div>
                  <div className={`pnl-badge ${isPositive ? 'positive' : 'negative'}`}>
                    {isPositive ? '+' : ''}{formatCurrency(holding.pnl)} ({formatPercent(holding.pnl_percent)})
                  </div>
                </div>

                <div className="holding-details">
                  <div className="holding-detail-item">
                    <div className="detail-label">Quantity</div>
                    <div className="detail-value">{holding.quantity}</div>
                  </div>
                  <div className="holding-detail-item">
                    <div className="detail-label">Current Value</div>
                    <div className="detail-value">{formatCurrency(holding.current_value)}</div>
                  </div>
                  <div className="holding-detail-item">
                    <div className="detail-label">Avg Buy Price</div>
                    <div className="detail-value">{formatCurrency(holding.avg_buy_price)}</div>
                  </div>
                  <div className="holding-detail-item">
                    <div className="detail-label">Current Price</div>
                    <div className="detail-value">{formatCurrency(holding.current_price)}</div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="empty-state">
          <Briefcase />
          <h3>No Holdings Yet</h3>
          <p>You haven't bought any stocks yet. Head over to the market to start investing.</p>
          <button 
            className="btn-primary" 
            style={{ width: 'auto', marginTop: '16px', padding: '12px 24px' }}
            onClick={() => navigate('/stocks')}
          >
            Explore Market
          </button>
        </div>
      )}
    </div>
  );
}

export default Portfolio;
