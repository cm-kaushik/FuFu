import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { formatCurrency } from '../utils/formatters';

const PERIODS = [
  { label: '1D', value: '1d' },
  { label: '5D', value: '5d' },
  { label: '1M', value: '1mo' },
  { label: '3M', value: '3mo' },
  { label: '6M', value: '6mo' },
  { label: '1Y', value: '1y' },
  { label: '5Y', value: '5y' },
];

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: 'rgba(22, 27, 45, 0.95)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '10px',
        padding: '12px 16px',
        backdropFilter: 'blur(10px)',
      }}>
        <p style={{ fontSize: '0.75rem', color: '#8b95a8', marginBottom: '4px' }}>{label}</p>
        <p style={{ fontSize: '1rem', fontWeight: 700, color: '#00d4aa' }}>
          {formatCurrency(payload[0].value)}
        </p>
        {payload[0].payload.volume && (
          <p style={{ fontSize: '0.72rem', color: '#5a6478', marginTop: '4px' }}>
            Vol: {new Intl.NumberFormat('en-IN').format(payload[0].payload.volume)}
          </p>
        )}
      </div>
    );
  }
  return null;
}

function PriceChart({ data, period, onPeriodChange, title = 'Price Chart' }) {
  const isPositive = data.length >= 2 ? data[data.length - 1].close >= data[0].close : true;
  const chartColor = isPositive ? '#00d4aa' : '#ff6b6b';

  return (
    <div className="chart-container">
      <div className="chart-header">
        <h3 className="dashboard-section-title">{title}</h3>
        <div className="chart-periods">
          {PERIODS.map((p) => (
            <button
              key={p.value}
              className={`chart-period-btn ${period === p.value ? 'active' : ''}`}
              onClick={() => onPeriodChange(p.value)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {data.length > 0 ? (
        <ResponsiveContainer width="100%" height={350}>
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={chartColor} stopOpacity={0.3} />
                <stop offset="100%" stopColor={chartColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: '#5a6478' }}
              axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#5a6478' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `₹${v.toLocaleString('en-IN')}`}
              domain={['auto', 'auto']}
              width={80}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="close"
              stroke={chartColor}
              strokeWidth={2}
              fill="url(#chartGradient)"
              animationDuration={800}
            />
          </AreaChart>
        </ResponsiveContainer>
      ) : (
        <div style={{ height: 350, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#5a6478' }}>
          Loading chart data...
        </div>
      )}
    </div>
  );
}

export default PriceChart;
