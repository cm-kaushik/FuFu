import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, TrendingUp, Briefcase, ArrowLeftRight, User, BarChart3, Plus, Layers } from 'lucide-react';

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">SV</div>
        <div>
          <h1>FUFU</h1>
          <span>NSE Trading</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Main Menu</div>

        <NavLink to="/" end className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <LayoutDashboard size={20} />
          Dashboard
        </NavLink>

        <NavLink to="/stocks" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <TrendingUp size={20} />
          Stocks
        </NavLink>

        <NavLink to="/portfolio" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <Briefcase size={20} />
          Portfolio
        </NavLink>

        <NavLink to="/transactions" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <ArrowLeftRight size={20} />
          Transactions
        </NavLink>

        <div className="sidebar-section-label">Custom Indexes</div>

        <NavLink to="/indexes" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <Layers size={20} />
          My Indexes
        </NavLink>

        <NavLink to="/indexes/create" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <Plus size={20} />
          Create Index
        </NavLink>

        <div className="sidebar-section-label">Account</div>

        <NavLink to="/profile" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <User size={20} />
          Profile
        </NavLink>
      </nav>
    </aside>
  );
}

export default Sidebar;
