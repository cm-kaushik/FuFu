import { useState, useEffect } from 'react';
import { getStockDetail, getStockHistory } from '../services/stockApi';

export function useStock(symbol) {
  const [stock, setStock] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [period, setPeriod] = useState('1mo');

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    setError(null);

    getStockDetail(symbol)
      .then((res) => setStock(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to fetch stock data'))
      .finally(() => setLoading(false));
  }, [symbol]);

  useEffect(() => {
    if (!symbol) return;

    getStockHistory(symbol, period)
      .then((res) => setHistory(res.data))
      .catch((err) => console.error('Failed to fetch history:', err));
  }, [symbol, period]);

  return { stock, history, loading, error, period, setPeriod };
}

export default useStock;
