import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

function NavChart({ history }) {
  if (!history || history.length === 0) {
    return (
      <div className="chart-empty">
        <p>Performance data will appear after investment</p>
      </div>
    );
  }

  const data = history.map(h => ({
    date: h.date ? new Date(h.date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }) : '',
    nav: h.nav,
    value: h.total_value,
  }));

  const firstNav = data[0]?.nav || 100;
  const lastNav = data[data.length - 1]?.nav || 100;
  const isPositive = lastNav >= firstNav;

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="chart-tooltip">
          <p className="chart-tooltip-label">{label}</p>
          <p className="chart-tooltip-value">NAV: ₹{payload[0].value.toFixed(2)}</p>
          {payload[0].payload.value > 0 && (
            <p className="chart-tooltip-desc">Value: ₹{payload[0].payload.value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</p>
          )}
        </div>
      );
    }
    return null;
  };

  const gradientColor = isPositive ? '#00c853' : '#ff1744';

  return (
    <div className="nav-chart">
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="navGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={gradientColor} stopOpacity={0.3} />
              <stop offset="95%" stopColor={gradientColor} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="date"
            stroke="#666"
            fontSize={11}
            tickLine={false}
          />
          <YAxis
            stroke="#666"
            fontSize={11}
            tickLine={false}
            domain={['dataMin - 5', 'dataMax + 5']}
            tickFormatter={(v) => `₹${v}`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="nav"
            stroke={gradientColor}
            strokeWidth={2}
            fill="url(#navGradient)"
            animationDuration={800}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export default NavChart;
