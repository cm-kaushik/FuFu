import api from './api';

// ============================================================
// INDEX CRUD
// ============================================================

export const createIndex = (data) =>
  api.post('/indexes', data);

export const getIndexes = () =>
  api.get('/indexes');

export const getIndexDetail = (indexId) =>
  api.get(`/indexes/${indexId}`);

export const deleteIndex = (indexId) =>
  api.delete(`/indexes/${indexId}`);

// ============================================================
// INDEX BUILDER HELPERS
// ============================================================

export const getThemes = () =>
  api.get('/indexes/themes');

export const getSectors = () =>
  api.get('/indexes/sectors');

export const getStocksBySector = (sector = '', search = '') => {
  let url = '/indexes/stocks-by-sector?';
  if (sector) url += `sector=${encodeURIComponent(sector)}&`;
  if (search) url += `search=${encodeURIComponent(search)}`;
  return api.get(url);
};

// ============================================================
// INVESTMENT
// ============================================================

export const investInIndex = (indexId, amount, pin) =>
  api.post(`/indexes/${indexId}/invest`, { amount, pin });

export const redeemFromIndex = (indexId, amount, pin, redeemAll = false) =>
  api.post(`/indexes/${indexId}/redeem`, { amount, pin, redeem_all: redeemAll });

// ============================================================
// REBALANCE
// ============================================================

export const rebalanceIndex = (indexId, pin) =>
  api.post(`/indexes/${indexId}/rebalance`, { pin });

export const getRebalanceHistory = (indexId) =>
  api.get(`/indexes/${indexId}/rebalance-history`);
