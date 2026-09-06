import api from './api';

export const buyStock = (symbol, quantity, pin) =>
  api.post('/transactions/buy', { symbol, quantity, pin });

export const sellStock = (symbol, quantity, pin) =>
  api.post('/transactions/sell', { symbol, quantity, pin });

export const addFunds = (amount, pin) =>
  api.post('/transactions/add-funds', { amount, pin });

export const getTransactions = (limit = 50, offset = 0, type = null) => {
  let url = `/transactions/history?limit=${limit}&offset=${offset}`;
  if (type) url += `&type=${type}`;
  return api.get(url);
};
