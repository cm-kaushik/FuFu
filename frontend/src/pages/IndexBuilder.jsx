import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Plus, ChevronRight, ChevronLeft, Check, Layers, Target, BarChart3, Zap } from 'lucide-react';
import { createIndex, getSectors, getStocksBySector } from '../services/indexApi';
import { formatCurrency } from '../utils/formatters';

const WEIGHT_STRATEGIES = [
  { value: 'EQUAL', label: 'Equal Weight', icon: '⚖️', desc: 'Each stock gets the same allocation percentage' },
  { value: 'MARKET_CAP', label: 'Market Cap Weight', icon: '📊', desc: 'Allocate proportionally by stock price (market cap proxy)' },
  { value: 'CUSTOM', label: 'Custom Weight', icon: '🎯', desc: 'You set the exact percentage for each stock' },
  { value: 'PERFORMANCE', label: 'Performance Weight', icon: '🚀', desc: 'Higher weight to top-performing stocks' },
];

function IndexBuilder() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Step 1: Sector
  const [sectors, setSectors] = useState([]);
  const [selectedSector, setSelectedSector] = useState('');

  // Step 2: Stock Selection
  const [availableStocks, setAvailableStocks] = useState([]);
  const [selectedStocks, setSelectedStocks] = useState([]);
  const [stockSearch, setStockSearch] = useState('');
  const [stocksLoading, setStocksLoading] = useState(false);

  // Step 3: Top-N & Strategy
  const [topN, setTopN] = useState(3);
  const [weightStrategy, setWeightStrategy] = useState('EQUAL');
  const [customWeights, setCustomWeights] = useState([]);

  // Step 4: Name & Description
  const [indexName, setIndexName] = useState('');
  const [indexDescription, setIndexDescription] = useState('');

  // Load sectors
  useEffect(() => {
    const loadData = async () => {
      try {
        const sectorsRes = await getSectors();
        setSectors(sectorsRes.data.sectors || []);
      } catch (err) {
        console.error('Failed to load sectors:', err);
      }
    };
    loadData();
  }, []);

  // Load stocks when sector changes
  useEffect(() => {
    let isMounted = true;
    const loadStocks = async () => {
      setStocksLoading(true);
      try {
        const res = await getStocksBySector(selectedSector, stockSearch);
        if (isMounted) {
          const stocks = res.data.stocks || [];
          setAvailableStocks(stocks);
          // Pre-select Top 5 flagship stocks if nothing is selected yet and no search query active
          if (!stockSearch && selectedStocks.length === 0 && stocks.length >= 2) {
            const initialN = Math.min(5, stocks.length);
            setSelectedStocks(stocks.slice(0, initialN));
            setTopN(initialN);
          }
        }
      } catch (err) {
        console.error('Failed to load stocks:', err);
      } finally {
        if (isMounted) setStocksLoading(false);
      }
    };

    const timer = setTimeout(loadStocks, 300);
    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [selectedSector, stockSearch]);

  // Update custom weights when topN changes
  useEffect(() => {
    if (weightStrategy === 'CUSTOM') {
      const equalWeight = parseFloat((100 / topN).toFixed(2));
      setCustomWeights(Array(topN).fill(equalWeight));
    }
  }, [topN, weightStrategy]);

  const toggleStock = (stock) => {
    setSelectedStocks(prev => {
      const exists = prev.find(s => s.symbol === stock.symbol);
      let updated;
      if (exists) {
        updated = prev.filter(s => s.symbol !== stock.symbol);
      } else {
        updated = [...prev, stock];
      }
      if (updated.length > 0 && topN > updated.length) {
        setTopN(updated.length);
      }
      return updated;
    });
  };

  const handleSelectTopN = (n) => {
    const count = Math.min(n, availableStocks.length);
    const topSlice = availableStocks.slice(0, count);
    setSelectedStocks(topSlice);
    setTopN(count);
  };

  const handleSelectAll = () => {
    setSelectedStocks([...availableStocks]);
    setTopN(Math.min(topN, availableStocks.length) || Math.min(5, availableStocks.length));
  };

  const handleClearAll = () => {
    setSelectedStocks([]);
    setTopN(3);
  };

  const handleAdjustTopN = (delta) => {
    const maxLimit = Math.max(availableStocks.length, selectedStocks.length, 1);
    const newN = Math.max(1, Math.min(topN + delta, maxLimit));
    if (selectedStocks.length < newN && availableStocks.length >= newN) {
      const notSelected = availableStocks.filter(s => !selectedStocks.some(sel => sel.symbol === s.symbol));
      const toAdd = notSelected.slice(0, newN - selectedStocks.length);
      setSelectedStocks(prev => [...prev, ...toAdd]);
    }
    setTopN(newN);
  };

  const handleCustomWeightChange = (idx, value) => {
    const newWeights = [...customWeights];
    newWeights[idx] = parseFloat(value) || 0;
    setCustomWeights(newWeights);
  };

  const handleCreate = async () => {
    setError('');
    setSuccess('');

    if (!indexName.trim()) {
      setError('Please enter a name for your index.');
      return;
    }

    setLoading(true);

    try {
      const data = {
        name: indexName,
        description: indexDescription,
        sector: selectedSector || null,
        theme: selectedSector || null,
        stock_symbols: selectedStocks.map(s => s.symbol),
        top_n: topN,
        weight_strategy: weightStrategy,
        custom_weights: weightStrategy === 'CUSTOM' ? customWeights : null,
      };

      const res = await createIndex(data);
      setSuccess(res.data.message);

      setTimeout(() => {
        navigate('/indexes');
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create index.');
    } finally {
      setLoading(false);
    }
  };

  const canProceed = () => {
    switch (step) {
      case 1: return true;
      case 2: return selectedStocks.length >= 2;
      case 3: return topN >= 1 && topN <= selectedStocks.length;
      case 4: return indexName.trim().length >= 2;
      default: return false;
    }
  };

  const generateName = () => {
    const sectorClean = selectedSector
      ? selectedSector.replace(' & Financial Services', '').replace('Information Technology (IT)', 'IT')
      : 'Diversified';
    setIndexName(`${sectorClean} Top ${topN}`);
  };

  return (
    <div>
      <div className="page-header">
        <h1>🏗️ Create Custom Index</h1>
        <p>Build your own sector-based index (like NIFTY Bank or NIFTY IT) — customized with your favorite stocks and weights.</p>
      </div>

      {/* Progress Steps */}
      <div className="wizard-progress">
        {[
          { num: 1, label: 'Sector' },
          { num: 2, label: 'Stocks' },
          { num: 3, label: 'Strategy' },
          { num: 4, label: 'Review' },
        ].map(s => (
          <div
            key={s.num}
            className={`wizard-step ${step === s.num ? 'active' : ''} ${step > s.num ? 'completed' : ''}`}
            onClick={() => { if (s.num < step) setStep(s.num); }}
          >
            <div className="wizard-step-circle">
              {step > s.num ? <Check size={16} /> : s.num}
            </div>
            <span className="wizard-step-label">{s.label}</span>
          </div>
        ))}
      </div>

      {error && <div className="form-error" style={{ marginBottom: '16px' }}>{error}</div>}
      {success && <div className="form-success" style={{ marginBottom: '16px' }}>{success}</div>}

      {/* Step 1: Sector Selection */}
      {step === 1 && (
        <div className="wizard-content">
          <div className="card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                <Target size={20} /> Choose an Indian Stock Market Sector
              </h3>
              {selectedSector && (
                <button
                  className="btn-outline btn-sm"
                  onClick={() => setSelectedSector('')}
                  style={{ fontSize: '12px' }}
                >
                  Clear Selection (Show All)
                </button>
              )}
            </div>
            <p className="text-muted" style={{ marginBottom: '20px' }}>
              Select an official NSE/BSE sector to build your index. Stocks in Step 2 will be filtered to this sector.
            </p>

            <div className="sector-grid">
              {sectors.map(sector => {
                const isSelected = selectedSector === sector.name;
                return (
                  <div
                    key={sector.id || sector.name}
                    className={`sector-card ${isSelected ? 'selected' : ''}`}
                    onClick={() => {
                      const newSec = isSelected ? '' : sector.name;
                      setSelectedSector(newSec);
                      setSelectedStocks([]); // Reset selected stocks on sector change
                    }}
                  >
                    <div className="sector-card-header">
                      <span className="sector-card-icon">{sector.icon || '📈'}</span>
                      <span className="sector-card-badge">
                        {sector.stock_count ? `${sector.stock_count} stocks` : 'Sector'}
                      </span>
                    </div>

                    <div className="sector-card-title">{sector.name}</div>
                    <div className="sector-card-desc">{sector.description}</div>

                    <div className="sector-card-footer">
                      <span className="sector-card-leaders" title={sector.leaders}>
                        {sector.leaders ? `Key: ${sector.leaders}` : 'Indian Market Leaders'}
                      </span>
                      {isSelected && <span style={{ color: 'var(--accent-primary)', fontWeight: 'bold' }}>✓ Selected</span>}
                    </div>
                  </div>
                );
              })}
            </div>

            {selectedSector && (
              <div className="sector-selected-banner">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ color: 'var(--accent-primary)', fontSize: '18px', fontWeight: 'bold' }}>✓</span>
                  <div>
                    <strong>Selected Sector:</strong> {selectedSector}
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      Click &ldquo;Next: Select Stocks&rdquo; below to pick your top companies from this sector.
                    </div>
                  </div>
                </div>
                <button
                  className="btn-outline btn-sm"
                  onClick={() => {
                    setSelectedSector('');
                    setSelectedStocks([]);
                  }}
                  style={{ fontSize: '12px' }}
                  type="button"
                >
                  Clear Selection
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Step 2: Stock Selection */}
      {step === 2 && (
        <div className="wizard-content">
          <div className="card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
              <div>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                  📈 Select Stocks ({selectedStocks.length} selected)
                </h3>
                <p className="text-muted" style={{ margin: '4px 0 0', fontSize: '13px' }}>
                  {selectedSector ? (
                    <>Showing stocks in <strong>{selectedSector}</strong>. Select at least 2 stocks for your index universe.</>
                  ) : (
                    <>Showing all sectors. Select at least 2 stocks for your index universe.</>
                  )}
                </p>
              </div>
              {selectedSector && (
                <button
                  className="btn-outline btn-sm"
                  onClick={() => setStep(1)}
                  style={{ fontSize: '12px' }}
                >
                  Change Sector
                </button>
              )}
            </div>

            {/* Quick Select Top N Bar */}
            <div className="step2-topn-panel">
              <div className="step2-topn-left">
                <span className="step2-topn-label">
                  <Zap size={16} style={{ color: 'var(--accent-primary)' }} /> Select Top N:
                </span>
                <div className="step2-topn-presets">
                  {[3, 5, 8, 10].map(n => {
                    const isPresetActive = topN === n && selectedStocks.length >= n;
                    return (
                      <button
                        key={n}
                        type="button"
                        className={`step2-preset-btn ${isPresetActive ? 'active' : ''}`}
                        onClick={() => handleSelectTopN(n)}
                        disabled={availableStocks.length < n}
                        title={`Select top ${n} flagship leaders`}
                      >
                        Top {n}
                      </button>
                    );
                  })}
                  <button
                    type="button"
                    className={`step2-preset-btn ${selectedStocks.length === availableStocks.length && availableStocks.length > 0 ? 'active' : ''}`}
                    onClick={handleSelectAll}
                    disabled={availableStocks.length === 0}
                  >
                    All ({availableStocks.length})
                  </button>
                  {selectedStocks.length > 0 && (
                    <button
                      type="button"
                      className="btn-outline btn-sm"
                      onClick={handleClearAll}
                      style={{ fontSize: '11px', padding: '4px 8px' }}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              <div className="step2-topn-right">
                <div className="step2-stepper-wrap">
                  <span className="step2-stepper-title">Active in Index:</span>
                  <button
                    type="button"
                    className="step2-stepper-btn"
                    onClick={() => handleAdjustTopN(-1)}
                    disabled={topN <= 1}
                  >
                    -
                  </button>
                  <span className="step2-stepper-val">{topN}</span>
                  <button
                    type="button"
                    className="step2-stepper-btn"
                    onClick={() => handleAdjustTopN(1)}
                    disabled={topN >= Math.max(availableStocks.length, selectedStocks.length)}
                  >
                    +
                  </button>
                </div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  ({selectedStocks.length} in universe)
                </span>
              </div>
            </div>

            <div className="stock-search-bar" style={{ marginBottom: '16px' }}>
              <Search size={18} />
              <input
                type="text"
                placeholder="Search stocks by name or symbol..."
                value={stockSearch}
                onChange={(e) => setStockSearch(e.target.value)}
                className="form-input"
                style={{ paddingLeft: '36px' }}
              />
            </div>

            {/* Selected stocks chips */}
            {selectedStocks.length > 0 && (
              <div className="selected-stocks-bar">
                {selectedStocks.map(s => (
                  <span key={s.symbol} className="selected-stock-chip" onClick={() => toggleStock(s)}>
                    {s.symbol.replace('.NS', '')} ✕
                  </span>
                ))}
              </div>
            )}

            {/* Available stocks */}
            <div className="stock-selection-list">
              {stocksLoading ? (
                <div className="loading-screen" style={{ height: '200px', background: 'transparent' }}>
                  <div className="loading-spinner"></div>
                </div>
              ) : (
                availableStocks.map(stock => {
                  const selectedIndex = selectedStocks.findIndex(s => s.symbol === stock.symbol);
                  const isSelected = selectedIndex !== -1;
                  const isActive = isSelected && selectedIndex < topN;
                  return (
                    <div
                      key={stock.symbol}
                      className={`stock-selection-item ${isSelected ? 'selected' : ''}`}
                      onClick={() => toggleStock(stock)}
                    >
                      <div className="stock-selection-check">
                        {isSelected && <Check size={16} />}
                      </div>
                      <div className="stock-selection-info">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span className="stock-selection-symbol">{stock.symbol.replace('.NS', '')}</span>
                          {isSelected && (
                            <span className={`stock-rank-badge ${isActive ? 'active' : 'reserve'}`}>
                              {isActive ? `#${selectedIndex + 1} Active` : `#${selectedIndex + 1} Reserve`}
                            </span>
                          )}
                        </div>
                        <span className="stock-selection-name">{stock.name}</span>
                      </div>
                      <div className="stock-selection-sector">{stock.sector}</div>
                      <div className="stock-selection-price">
                        {stock.current_price ? formatCurrency(stock.current_price) : '—'}
                        {stock.change_percent != null && (
                          <span className={stock.change_percent >= 0 ? 'text-green' : 'text-red'}>
                            {stock.change_percent >= 0 ? '+' : ''}{stock.change_percent}%
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
              {!stocksLoading && availableStocks.length === 0 && (
                <p className="text-muted" style={{ textAlign: 'center', padding: '32px' }}>
                  No stocks found. Try a different sector or search term.
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Step 3: Top-N & Weight Strategy */}
      {step === 3 && (
        <div className="wizard-content">
          <div className="card" style={{ padding: '24px' }}>
            <h3 style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BarChart3 size={20} /> Select Top N
            </h3>
            <p className="text-muted" style={{ marginBottom: '16px' }}>
              You selected {selectedStocks.length} stocks. How many should be in the active index?
              The system will auto-pick the top {topN} by market cap.
            </p>

            <div className="topn-selector">
              {Array.from({ length: selectedStocks.length }, (_, i) => i + 1).map(n => (
                <button
                  key={n}
                  className={`topn-btn ${topN === n ? 'selected' : ''}`}
                  onClick={() => setTopN(n)}
                >
                  Top {n}
                </button>
              ))}
            </div>
          </div>

          <div className="card" style={{ padding: '24px', marginTop: '16px' }}>
            <h3 style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Zap size={20} /> Weight Strategy
            </h3>
            <p className="text-muted" style={{ marginBottom: '16px' }}>
              How should your investment be distributed among the top {topN} stocks?
            </p>

            <div className="strategy-grid">
              {WEIGHT_STRATEGIES.map(ws => (
                <div
                  key={ws.value}
                  className={`strategy-card ${weightStrategy === ws.value ? 'selected' : ''}`}
                  onClick={() => setWeightStrategy(ws.value)}
                >
                  <div className="strategy-icon">{ws.icon}</div>
                  <div className="strategy-label">{ws.label}</div>
                  <div className="strategy-desc">{ws.desc}</div>
                </div>
              ))}
            </div>

            {weightStrategy === 'CUSTOM' && (
              <div className="custom-weights" style={{ marginTop: '16px' }}>
                <h4>Set Custom Weights (must total 100%)</h4>
                <p className="text-muted" style={{ fontSize: '12px', marginBottom: '8px' }}>
                  Total: {customWeights.reduce((a, b) => a + b, 0).toFixed(2)}%
                </p>
                {selectedStocks.slice(0, topN).map((stock, idx) => (
                  <div key={stock.symbol} className="custom-weight-row">
                    <span>{stock.symbol.replace('.NS', '')}</span>
                    <input
                      type="number"
                      value={customWeights[idx] || 0}
                      onChange={(e) => handleCustomWeightChange(idx, e.target.value)}
                      min="0" max="100" step="0.5"
                      className="form-input"
                      style={{ width: '100px' }}
                    />
                    <span>%</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Step 4: Review & Create */}
      {step === 4 && (
        <div className="wizard-content">
          <div className="card" style={{ padding: '24px' }}>
            <h3 style={{ marginBottom: '16px' }}>📝 Name Your Index</h3>

            <div className="form-group">
              <label>Index Name</label>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g., EV Top 3, Energy Top 5"
                  value={indexName}
                  onChange={(e) => setIndexName(e.target.value)}
                />
                <button className="btn-outline" onClick={generateName} type="button">
                  Auto
                </button>
              </div>
            </div>

            <div className="form-group">
              <label>Description (optional)</label>
              <textarea
                className="form-input"
                placeholder="Describe your investment strategy..."
                value={indexDescription}
                onChange={(e) => setIndexDescription(e.target.value)}
                rows={3}
              />
            </div>
          </div>

          <div className="card" style={{ padding: '24px', marginTop: '16px' }}>
            <h3 style={{ marginBottom: '16px' }}>📋 Review Your Index</h3>

            <div className="review-grid">
              <div className="review-item">
                <span className="review-label">Sector</span>
                <span className="review-value">{selectedSector || 'Diversified (All Sectors)'}</span>
              </div>
              <div className="review-item">
                <span className="review-label">Market</span>
                <span className="review-value">NSE / BSE (India)</span>
              </div>
              <div className="review-item">
                <span className="review-label">Universe</span>
                <span className="review-value">{selectedStocks.length} stocks</span>
              </div>
              <div className="review-item">
                <span className="review-label">Active Index</span>
                <span className="review-value">Top {topN}</span>
              </div>
              <div className="review-item">
                <span className="review-label">Strategy</span>
                <span className="review-value">{WEIGHT_STRATEGIES.find(w => w.value === weightStrategy)?.label}</span>
              </div>
              <div className="review-item">
                <span className="review-label">Rebalance</span>
                <span className="review-value">Semi-Annual (Mar/Sep)</span>
              </div>
            </div>

            <h4 style={{ marginTop: '16px', marginBottom: '8px' }}>Selected Stocks:</h4>
            <div className="review-stocks">
              {selectedStocks.map((stock, idx) => (
                <div key={stock.symbol} className={`review-stock-item ${idx < topN ? 'active' : 'inactive'}`}>
                  <span className="review-stock-rank">#{idx + 1}</span>
                  <span className="review-stock-symbol">{stock.symbol.replace('.NS', '')}</span>
                  <span className="review-stock-name">{stock.name}</span>
                  {idx < topN && <span className="review-stock-badge">Active</span>}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="wizard-nav">
        {step > 1 && (
          <button className="btn-outline" onClick={() => setStep(step - 1)}>
            <ChevronLeft size={18} /> Back
          </button>
        )}
        <div style={{ flex: 1 }} />
        {step < 4 ? (
          <button
            className="btn-primary"
            onClick={() => setStep(step + 1)}
            disabled={!canProceed()}
          >
            {step === 1 && selectedSector ? 'Next: Select Stocks' : 'Next'} <ChevronRight size={18} />
          </button>
        ) : (
          <button
            className="btn-primary btn-create-index"
            onClick={handleCreate}
            disabled={loading || !canProceed()}
          >
            {loading ? 'Creating...' : '🚀 Create Index'}
          </button>
        )}
      </div>
    </div>
  );
}

export default IndexBuilder;
