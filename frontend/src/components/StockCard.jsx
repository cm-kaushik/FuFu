import React from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { formatCurrency, displaySymbol } from '../utils/formatters';

function StockCard({ stock }) {
  const navigate = useNavigate();
  const isPositive = (stock.change || 0) >= 0;

  return (
    <div
      className="stock-card"
      onClick={() => navigate(`/stocks/${stock.symbol}`)}
      id={`stock-card-${stock.symbol}`}
    >
      <div className="stock-header">
        <span className="stock-symbol">{displaySymbol(stock.symbol)}</span>
        <span className="stock-exchange">{stock.exchange || 'NSE'}</span>
      </div>

      <div className="stock-name">{stock.name}</div>

      <div className="stock-price">
        {stock.current_price ? formatCurrency(stock.current_price) : '—'}
      </div>

      <div className={`stock-change ${isPositive ? 'positive' : 'negative'}`}>
        {isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
        {stock.change !== null && stock.change !== undefined
          ? `${isPositive ? '+' : ''}${stock.change.toFixed(2)} (${isPositive ? '+' : ''}${(stock.change_percent || 0).toFixed(2)}%)`
          : 'Loading...'}
      </div>

      {stock.sector && <div className="stock-sector">{stock.sector}</div>}
    </div>
  );
}

export default StockCard;
