import React, { useState, useEffect } from 'react';
import { getAllStocks } from '../services/stockApi';
import StockCard from '../components/StockCard';
import StockSearch from '../components/StockSearch';
import { TrendingUp } from 'lucide-react';

function Stocks() {
  const [stocks, setStocks] = useState([]);
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);

  useEffect(() => {
    // Removed getAllStocks() to stop listing all stocks on page load.
    // The page will now wait for the user to search.
    setLoading(false);
  }, []);

  const handleSearchResults = (results) => {
    setSearchResults(results);
  };

  const displayStocks = searchResults !== null ? searchResults : stocks;

  return (
    <div>
      <div className="page-header">
        <h1>Market Overview</h1>
        <p>Explore and trade Indian NSE/BSE stocks.</p>
      </div>

      <StockSearch onResults={handleSearchResults} onLoading={setSearchLoading} />

      {loading || searchLoading ? (
        <div className="loading-screen" style={{ height: '30vh', background: 'transparent' }}>
          <div className="loading-spinner"></div>
        </div>
      ) : displayStocks.length > 0 ? (
        <div className="stocks-grid">
          {displayStocks.map((stock) => (
            <StockCard key={stock.symbol} stock={stock} />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <TrendingUp />
          <h3>No stocks found</h3>
          <p>Try searching for a different stock name or symbol.</p>
        </div>
      )}
    </div>
  );
}

export default Stocks;
