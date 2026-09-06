import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { formatCurrency } from '../utils/formatters';
import { Wallet, Plus, User, LogOut } from 'lucide-react';
import { addFunds } from '../services/transactionApi';

function Navbar() {
  const { user, logout, updateBalance } = useAuth();
  const [showFundsModal, setShowFundsModal] = useState(false);
  const [fundAmount, setFundAmount] = useState('');
  const [fundPin, setFundPin] = useState('');
  const [fundError, setFundError] = useState('');
  const [fundSuccess, setFundSuccess] = useState('');
  const [fundLoading, setFundLoading] = useState(false);

  const handleAddFunds = async (e) => {
    e.preventDefault();
    setFundError('');
    setFundSuccess('');
    setFundLoading(true);

    try {
      const res = await addFunds(parseFloat(fundAmount), fundPin);
      setFundSuccess(res.data.message);
      updateBalance(res.data.new_balance);
      setFundAmount('');
      setFundPin('');
      setTimeout(() => {
        setShowFundsModal(false);
        setFundSuccess('');
      }, 1500);
    } catch (err) {
      setFundError(err.response?.data?.detail || 'Failed to add funds');
    } finally {
      setFundLoading(false);
    }
  };

  return (
    <>
      <nav className="navbar">
        <div className="navbar-left">
          <div className="navbar-greeting">
            <h2>Welcome back, {user?.username || 'Trader'} 👋</h2>
            <p>Indian Stock Market • NSE/BSE</p>
          </div>
        </div>

        <div className="navbar-right">
          <div className="navbar-balance">
            <div>
              <div className="balance-label">Available Balance</div>
              <div className="balance-amount">{formatCurrency(user?.balance || 0)}</div>
            </div>
            <Wallet size={20} />
          </div>

          <button className="add-funds-btn" onClick={() => setShowFundsModal(true)}>
            <Plus size={16} />
            Add Funds
          </button>

          <button className="navbar-btn" onClick={logout} title="Logout">
            <LogOut size={18} />
          </button>
        </div>
      </nav>

      {showFundsModal && (
        <div className="modal-overlay" onClick={() => setShowFundsModal(false)}>
          <div className="modal funds-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>💰 Add Funds</h2>
              <button className="modal-close" onClick={() => setShowFundsModal(false)}>✕</button>
            </div>

            {fundError && <div className="form-error">{fundError}</div>}
            {fundSuccess && <div className="form-success">{fundSuccess}</div>}

            <form onSubmit={handleAddFunds}>
              <div className="form-group">
                <label>Amount (₹)</label>
                <input
                  type="number"
                  className="form-input"
                  placeholder="Enter amount in rupees"
                  value={fundAmount}
                  onChange={(e) => setFundAmount(e.target.value)}
                  min="1"
                  required
                />
              </div>

              <div className="form-group">
                <label>Enter PIN to confirm</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="Enter 4-digit PIN"
                  value={fundPin}
                  onChange={(e) => setFundPin(e.target.value)}
                  maxLength={4}
                  required
                />
              </div>

              <button type="submit" className="btn-primary" disabled={fundLoading}>
                {fundLoading ? 'Processing...' : 'Add Funds'}
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

export default Navbar;
