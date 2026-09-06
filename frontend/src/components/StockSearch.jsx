import React, { useState, useEffect, useCallback } from 'react';
import { Search } from 'lucide-react';
import { searchStocks } from '../services/stockApi';

function StockSearch({ onResults, onLoading }) {
  const [query, setQuery] = useState('');

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      return;
    }

    onLoading?.(true);
    const timer = setTimeout(() => {
      searchStocks(query)
        .then((res) => {
          onResults?.(res.data);
        })
        .catch((err) => {
          console.error('Search error:', err);
        })
        .finally(() => {
          onLoading?.(false);
        });
    }, 400);

    return () => clearTimeout(timer);
  }, [query]);

  return (
    <div className="search-container">
      <div className="search-input-wrapper">
        <Search />
        <input
          id="stock-search-input"
          type="text"
          className="search-input"
          placeholder="Search stocks by name or symbol... (e.g., Reliance, TCS, INFY)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
    </div>
  );
}

export default StockSearch;
