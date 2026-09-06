import api from './api';

export const searchStocks = (query) => api.get(`/stocks/search?q=${query}`);

export const getPopularStocks = () => api.get('/stocks/popular');

export const getAllStocks = () => api.get('/stocks/all');

export const getStockDetail = (symbol) => api.get(`/stocks/${symbol}`);

export const getStockHistory = (symbol, period = '1mo') =>
  api.get(`/stocks/${symbol}/history?period=${period}`);
