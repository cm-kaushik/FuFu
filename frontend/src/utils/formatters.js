/**
 * Format number as Indian Rupees
 */
export function formatCurrency(amount) {
  if (amount === null || amount === undefined) return '₹0.00';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * Format large numbers (e.g., market cap)
 */
export function formatLargeNumber(num) {
  if (!num) return '—';
  if (num >= 1e12) return `₹${(num / 1e12).toFixed(2)}T`;
  if (num >= 1e9) return `₹${(num / 1e9).toFixed(2)}B`;
  if (num >= 1e7) return `₹${(num / 1e7).toFixed(2)}Cr`;
  if (num >= 1e5) return `₹${(num / 1e5).toFixed(2)}L`;
  return formatCurrency(num);
}

/**
 * Format date string
 */
export function formatDate(dateStr) {
  if (!dateStr) return '—';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

/**
 * Format date with time
 */
export function formatDateTime(dateStr) {
  if (!dateStr) return '—';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format percentage
 */
export function formatPercent(value) {
  if (value === null || value === undefined) return '0.00%';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * Format number
 */
export function formatNumber(num) {
  if (!num) return '0';
  return new Intl.NumberFormat('en-IN').format(num);
}

/**
 * Get display symbol (without .NS suffix)
 */
export function displaySymbol(symbol) {
  if (!symbol) return '';
  return symbol.replace('.NS', '').replace('.BO', '');
}
