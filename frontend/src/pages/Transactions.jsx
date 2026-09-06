import React, { useState, useEffect } from 'react';
import { getTransactions } from '../services/transactionApi';
import TransactionTable from '../components/TransactionTable';

function Transactions() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState(null);

  useEffect(() => {
    setLoading(true);
    getTransactions(100, 0, filter)
      .then((res) => setTransactions(res.data.transactions || []))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <div>
      <div className="page-header">
        <h1>Transactions</h1>
        <p>Your trading history and account deposits.</p>
      </div>

      {loading ? (
        <div className="loading-screen" style={{ height: '40vh', background: 'transparent' }}>
          <div className="loading-spinner"></div>
        </div>
      ) : (
        <TransactionTable 
          transactions={transactions} 
          filter={filter} 
          onFilterChange={setFilter} 
        />
      )}
    </div>
  );
}

export default Transactions;
