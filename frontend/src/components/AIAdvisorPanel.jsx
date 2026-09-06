import React from 'react';
import { X, AlertTriangle, TrendingUp, TrendingDown, Minus, Shield, Zap } from 'lucide-react';

const SENTIMENT_CONFIG = {
  BULLISH: { color: '#00c853', bg: 'rgba(0,200,83,0.1)', icon: <TrendingUp size={20} />, label: 'Bullish' },
  BEARISH: { color: '#ff1744', bg: 'rgba(255,23,68,0.1)', icon: <TrendingDown size={20} />, label: 'Bearish' },
  NEUTRAL: { color: '#ffc107', bg: 'rgba(255,193,7,0.1)', icon: <Minus size={20} />, label: 'Neutral' },
  CAUTIOUS: { color: '#ff9100', bg: 'rgba(255,145,0,0.1)', icon: <AlertTriangle size={20} />, label: 'Cautious' },
};

const RECOMMENDATION_COLORS = {
  BUY: '#00c853',
  SELL: '#ff1744',
  HOLD: '#ffc107',
  AVOID: '#ff1744',
};

function AIAdvisorPanel({ advice, loading, action, onClose }) {
  if (loading) {
    return (
      <div className="ai-advisor-panel">
        <div className="ai-advisor-header">
          <h3>🤖 AI Trading Advisor</h3>
          <button className="ai-close" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="ai-loading">
          <div className="ai-loading-pulse"></div>
          <p>Analyzing market conditions, news, and price trends...</p>
          <p className="text-muted" style={{ fontSize: '12px' }}>Powered by Groq AI</p>
        </div>
      </div>
    );
  }

  if (!advice) return null;

  const sentimentInfo = SENTIMENT_CONFIG[advice.sentiment] || SENTIMENT_CONFIG.NEUTRAL;
  const recColor = RECOMMENDATION_COLORS[advice.recommendation] || '#ffc107';

  return (
    <div className="ai-advisor-panel">
      <div className="ai-advisor-header">
        <h3>🤖 AI Trading Advisor</h3>
        <button className="ai-close" onClick={onClose}><X size={18} /></button>
      </div>

      {/* Recommendation & Sentiment */}
      <div className="ai-recommendation">
        <div className="ai-rec-main" style={{ borderColor: recColor }}>
          <span className="ai-rec-label">Recommendation</span>
          <span className="ai-rec-value" style={{ color: recColor }}>
            {advice.recommendation}
          </span>
        </div>

        <div className="ai-sentiment" style={{ background: sentimentInfo.bg }}>
          <span style={{ color: sentimentInfo.color }}>{sentimentInfo.icon}</span>
          <div>
            <span className="ai-sentiment-label">Sentiment</span>
            <span className="ai-sentiment-value" style={{ color: sentimentInfo.color }}>
              {sentimentInfo.label}
            </span>
          </div>
        </div>

        <div className="ai-confidence">
          <span className="ai-confidence-label">Confidence</span>
          <div className="ai-confidence-bar">
            <div
              className="ai-confidence-fill"
              style={{
                width: `${advice.confidence}%`,
                background: advice.confidence >= 70 ? '#00c853' : advice.confidence >= 40 ? '#ffc107' : '#ff1744',
              }}
            ></div>
          </div>
          <span className="ai-confidence-value">{advice.confidence}%</span>
        </div>
      </div>

      {/* Reasoning */}
      <div className="ai-section">
        <h4><Zap size={16} /> Analysis</h4>
        <p>{advice.reasoning}</p>
      </div>

      {/* Market Context */}
      {advice.market_context && (
        <div className="ai-section">
          <h4>📊 Market Context</h4>
          <p>{advice.market_context}</p>
        </div>
      )}

      {/* News Summary */}
      {advice.news_summary && (
        <div className="ai-section">
          <h4>📰 News Summary</h4>
          <p>{advice.news_summary}</p>
        </div>
      )}

      {/* Risk Assessment */}
      {advice.risk_assessment && (
        <div className="ai-section ai-risk">
          <h4><Shield size={16} /> Risk Assessment</h4>
          <p>{advice.risk_assessment}</p>
        </div>
      )}

      {/* Key Factors */}
      {advice.key_factors && advice.key_factors.length > 0 && (
        <div className="ai-section">
          <h4>🔑 Key Factors</h4>
          <ul className="ai-factors">
            {advice.key_factors.map((factor, idx) => (
              <li key={idx}>{factor}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Price Analysis */}
      {advice.price_analysis && Object.keys(advice.price_analysis).length > 0 && (
        <div className="ai-section">
          <h4>📈 Price Analysis</h4>
          <div className="ai-price-grid">
            {advice.price_analysis.support_level && (
              <div className="ai-price-item">
                <span className="label">Support</span>
                <span className="value">{advice.price_analysis.support_level}</span>
              </div>
            )}
            {advice.price_analysis.resistance_level && (
              <div className="ai-price-item">
                <span className="label">Resistance</span>
                <span className="value">{advice.price_analysis.resistance_level}</span>
              </div>
            )}
            {advice.price_analysis.trend && (
              <div className="ai-price-item">
                <span className="label">Trend</span>
                <span className="value">{advice.price_analysis.trend}</span>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="ai-disclaimer">
        ⚠️ AI advice is for informational purposes only. Always do your own research before trading.
      </div>
    </div>
  );
}

export default AIAdvisorPanel;
