import api from './api';

// ============================================================
// AI ADVISOR
// ============================================================

export const getAIAdvice = (data) =>
  api.post('/ai/advice', data);

export const getAdviceHistory = () =>
  api.get('/ai/history');

// ============================================================
// NEWS
// ============================================================

export const getStockNews = (symbol) =>
  api.get(`/ai/news/${symbol}`);

export const getSectorNews = (sector) =>
  api.get(`/ai/sector-news/${encodeURIComponent(sector)}`);
