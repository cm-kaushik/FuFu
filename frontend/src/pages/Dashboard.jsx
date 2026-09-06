import React, { useState, useEffect } from 'react';
import { getPortfolioSummary } from '../services/portfolioApi';
import { getPopularStocks } from '../services/stockApi';
import PortfolioCard from '../components/PortfolioCard';
import StockCard from '../components/StockCard';
import { formatCurrency } from '../utils/formatters';

function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [popularStocks, setPopularStocks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [summaryRes, popularRes] = await Promise.all([
          getPortfolioSummary(),
          getPopularStocks(),
        ]);
        setSummary(summaryRes.data);
        setPopularStocks(popularRes.data);
      } catch (err) {
        console.error('Dashboard error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="loading-screen" style={{ height: '50vh', background: 'transparent' }}>
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Your trading overview and market insights.</p>
      </div>

      <PortfolioCard summary={summary} />

      <div className="dashboard-section-title" style={{ marginTop: '32px' }}>
        Popular Stocks
      </div>
      
      <div className="stocks-grid">
        {popularStocks.map((stock) => (
          <StockCard key={stock.symbol} stock={stock} />
        ))}
      </div>
    </div>
  );
}

export default Dashboard;
