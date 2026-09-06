import React from 'react';
import { formatCurrency, formatDateTime, displaySymbol } from '../utils/formatters';

function TransactionTable({ transactions, showFilters = true, filter, onFilterChange }) {
  return (
    <div className="table-container">
      {showFilters && (
        <div className="table-header-bar">
          <h3 className="dashboard-section-title">Transaction History</h3>
          <div className="table-filters">
            {['ALL', 'BUY', 'SELL', 'DEPOSIT'].map((f) => (
              <button
                key={f}
                className={`filter-btn ${(filter || 'ALL') === f ? 'active' : ''}`}
                onClick={() => onFilterChange?.(f === 'ALL' ? null : f)}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      )}

      <table className="data-table">
        <thead>
          <tr>
            <th>Type</th>
            <th>Stock</th>
            <th>Quantity</th>
            <th>Price</th>
            <th>Total</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {transactions && transactions.length > 0 ? (
            transactions.map((t) => (
              <tr key={t.id}>
                <td>
                  <span className={`type-badge ${t.type.toLowerCase()}`}>
                    {t.type}
                  </span>
                </td>
                <td>
                  <div style={{ fontWeight: 600 }}>
                    {t.stock_symbol ? displaySymbol(t.stock_symbol) : '—'}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#5a6478' }}>
                    {t.stock_name || (t.type === 'DEPOSIT' ? 'Fund Deposit' : '')}
                  </div>
                </td>
                <td>{t.type === 'DEPOSIT' ? '—' : t.quantity}</td>
                <td>{t.type === 'DEPOSIT' ? '—' : formatCurrency(t.price_per_share)}</td>
                <td style={{ fontWeight: 600 }}>{formatCurrency(t.total_amount)}</td>
                <td style={{ fontSize: '0.82rem', color: '#8b95a8' }}>
                  {formatDateTime(t.created_at)}
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="6" style={{ textAlign: 'center', padding: '40px', color: '#5a6478' }}>
                No transactions found
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default TransactionTable;
