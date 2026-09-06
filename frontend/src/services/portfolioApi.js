import api from './api';

export const getPortfolio = () => api.get('/portfolio');

export const getPortfolioSummary = () => api.get('/portfolio/summary');
