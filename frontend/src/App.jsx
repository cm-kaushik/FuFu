import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Stocks from './pages/Stocks';
import StockDetails from './pages/StockDetails';
import Portfolio from './pages/Portfolio';
import Transactions from './pages/Transactions';
import Profile from './pages/Profile';
import MyIndexes from './pages/MyIndexes';
import IndexBuilder from './pages/IndexBuilder';
import IndexDetail from './pages/IndexDetail';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Loading FUFU...</p>
      </div>
    );
  }
  return user ? children : <Navigate to="/login" />;
}

function AppLayout({ children }) {
  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-content">
        <Navbar />
        <div className="page-content">
          {children}
        </div>
      </div>
    </div>
  );
}

function App() {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" /> : <Login />} />
      <Route path="/register" element={user ? <Navigate to="/" /> : <Register />} />

      <Route path="/" element={
        <ProtectedRoute>
          <AppLayout><Dashboard /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/stocks" element={
        <ProtectedRoute>
          <AppLayout><Stocks /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/stocks/:symbol" element={
        <ProtectedRoute>
          <AppLayout><StockDetails /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/portfolio" element={
        <ProtectedRoute>
          <AppLayout><Portfolio /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/transactions" element={
        <ProtectedRoute>
          <AppLayout><Transactions /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/profile" element={
        <ProtectedRoute>
          <AppLayout><Profile /></AppLayout>
        </ProtectedRoute>
      } />

      {/* Custom Index Routes */}
      <Route path="/indexes" element={
        <ProtectedRoute>
          <AppLayout><MyIndexes /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/indexes/create" element={
        <ProtectedRoute>
          <AppLayout><IndexBuilder /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/indexes/:id" element={
        <ProtectedRoute>
          <AppLayout><IndexDetail /></AppLayout>
        </ProtectedRoute>
      } />

      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

export default App;
