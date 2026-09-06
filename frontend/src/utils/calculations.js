/**
 * Calculate profit/loss
 */
export function calculatePnL(currentPrice, avgBuyPrice, quantity) {
  const invested = avgBuyPrice * quantity;
  const currentValue = currentPrice * quantity;
  const pnl = currentValue - invested;
  const pnlPercent = invested > 0 ? (pnl / invested) * 100 : 0;

  return {
    invested: Math.round(invested * 100) / 100,
    currentValue: Math.round(currentValue * 100) / 100,
    pnl: Math.round(pnl * 100) / 100,
    pnlPercent: Math.round(pnlPercent * 100) / 100,
  };
}

/**
 * Calculate total portfolio value
 */
export function calculatePortfolioValue(holdings) {
  return holdings.reduce((total, h) => total + h.current_value, 0);
}

/**
 * Calculate total invested
 */
export function calculateTotalInvested(holdings) {
  return holdings.reduce((total, h) => total + h.invested_value, 0);
}

/**
 * Calculate percentage change
 */
export function percentChange(current, previous) {
  if (!previous || previous === 0) return 0;
  return Math.round(((current - previous) / previous) * 100 * 100) / 100;
}
