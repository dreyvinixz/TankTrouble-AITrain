import React, { useState } from 'react';
import { MetricPoint } from '../types/telemetry';
import { TrendingUp, Activity } from 'lucide-react';

interface ChartsPanelProps {
  metrics: MetricPoint[];
}

export const ChartsPanel: React.FC<ChartsPanelProps> = ({ metrics }) => {
  const [activeTab, setActiveTab] = useState<'reward' | 'loss' | 'winrate'>('reward');
  const [hoverPoint, setHoverPoint] = useState<MetricPoint | null>(null);

  if (!metrics || metrics.length === 0) {
    return (
      <div className="glass-card" style={{ padding: '24px', textAlign: 'center', minHeight: '320px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <Activity size={32} color="#64748b" style={{ marginBottom: '12px' }} />
        <div style={{ color: '#94a3b8', fontSize: '0.95rem' }}>Aguardando métricas de treinamento...</div>
        <div style={{ color: '#64748b', fontSize: '0.8rem', marginTop: '4px' }}>Os gráficos serão plotados automaticamente conforme o PPO atualizar.</div>
      </div>
    );
  }

  // Dimensions for SVG plotting
  const width = 600;
  const height = 240;
  const padding = { top: 20, right: 30, bottom: 30, left: 50 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  // Extract series based on active tab
  let values1: number[] = [];
  let values2: number[] = [];
  let label1 = '';
  let label2 = '';
  let color1 = '#10b981';
  let color2 = '#38bdf8';

  if (activeTab === 'reward') {
    values1 = metrics.map((m) => m.mean_reward ?? 0);
    values2 = metrics.map((m) => m.max_reward ?? 0);
    label1 = 'Recompensa Média';
    label2 = 'Melhor Recompensa';
    color1 = '#34d399';
    color2 = '#fbbf24';
  } else if (activeTab === 'loss') {
    values1 = metrics.map((m) => m.policy_loss ?? 0);
    values2 = metrics.map((m) => m.value_loss ?? 0);
    label1 = 'Policy Loss';
    label2 = 'Value Loss';
    color1 = '#f43f5e';
    color2 = '#a78bfa';
  } else {
    values1 = metrics.map((m) => (m.win_rate ?? 0) * 100);
    label1 = 'Win Rate (%)';
    color1 = '#fbbf24';
  }

  const allVals = [...values1, ...(values2.length > 0 ? values2 : [])];
  const minVal = Math.min(...allVals, 0);
  const maxVal = Math.max(...allVals, 0.01);
  const valRange = maxVal - minVal || 1;

  const pointsToSvgPath = (vals: number[]) => {
    if (vals.length === 0) return '';
    return vals
      .map((v, i) => {
        const x = padding.left + (i / Math.max(vals.length - 1, 1)) * chartW;
        const y = padding.top + chartH - ((v - minVal) / valRange) * chartH;
        return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(' ');
  };

  const path1 = pointsToSvgPath(values1);
  const path2 = pointsToSvgPath(values2);

  // Area path for series 1
  const areaPath1 = values1.length > 0
    ? `${path1} L ${padding.left + chartW} ${padding.top + chartH} L ${padding.left} ${padding.top + chartH} Z`
    : '';

  return (
    <div className="glass-card" style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header with tabs */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <TrendingUp size={18} color="#10b981" />
          <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>
            Curvas de Aprendizado PPO
          </span>
        </div>

        {/* Tab Buttons */}
        <div style={{ display: 'flex', background: 'rgba(255, 255, 255, 0.04)', borderRadius: '8px', padding: '3px' }}>
          <button
            onClick={() => setActiveTab('reward')}
            style={{
              background: activeTab === 'reward' ? 'rgba(16, 185, 129, 0.2)' : 'transparent',
              color: activeTab === 'reward' ? '#34d399' : '#94a3b8',
              border: 'none', borderRadius: '6px', padding: '6px 14px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer'
            }}
          >
            Recompensa / Fitness
          </button>
          <button
            onClick={() => setActiveTab('loss')}
            style={{
              background: activeTab === 'loss' ? 'rgba(244, 63, 94, 0.2)' : 'transparent',
              color: activeTab === 'loss' ? '#fb7185' : '#94a3b8',
              border: 'none', borderRadius: '6px', padding: '6px 14px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer'
            }}
          >
            Perdas (Loss)
          </button>
          <button
            onClick={() => setActiveTab('winrate')}
            style={{
              background: activeTab === 'winrate' ? 'rgba(245, 158, 11, 0.2)' : 'transparent',
              color: activeTab === 'winrate' ? '#fbbf24' : '#94a3b8',
              border: 'none', borderRadius: '6px', padding: '6px 14px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer'
            }}
          >
            Win Rate %
          </button>
        </div>
      </div>

      {/* Legend & Hover Display */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8rem', color: '#94a3b8' }}>
        <div style={{ display: 'flex', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '2px', backgroundColor: color1 }} />
            <span>{label1}</span>
          </div>
          {label2 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '2px', backgroundColor: color2 }} />
              <span>{label2}</span>
            </div>
          )}
        </div>

        {hoverPoint && (
          <div className="mono" style={{ color: '#f8fafc', fontWeight: 600 }}>
            Update #{hoverPoint.update}: {activeTab === 'reward' ? `Mean: ${hoverPoint.mean_reward?.toFixed(2)} | Max: ${hoverPoint.max_reward?.toFixed(2)}` : activeTab === 'loss' ? `Pol: ${hoverPoint.policy_loss?.toFixed(4)} | Val: ${hoverPoint.value_loss?.toFixed(4)}` : `Win: ${(hoverPoint.win_rate! * 100).toFixed(1)}%`}
          </div>
        )}
      </div>

      {/* SVG Chart Area */}
      <div style={{ width: '100%', overflowX: 'auto' }}>
        <svg
          viewBox={`0 0 ${width} ${height}`}
          style={{ width: '100%', height: 'auto', minHeight: '220px', overflow: 'visible' }}
          onMouseLeave={() => setHoverPoint(null)}
        >
          <defs>
            <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={color1} stopOpacity="0.3" />
              <stop offset="100%" stopColor={color1} stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, idx) => {
            const y = padding.top + chartH * (1 - pct);
            const val = minVal + pct * valRange;
            return (
              <g key={idx}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={padding.left + chartW}
                  y2={y}
                  stroke="rgba(255, 255, 255, 0.05)"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 8}
                  y={y + 4}
                  textAnchor="end"
                  fill="#64748b"
                  fontSize="10"
                  className="mono"
                >
                  {val.toFixed(1)}
                </text>
              </g>
            );
          })}

          {/* X Axis labels */}
          {metrics.length > 0 && (
            <>
              <text x={padding.left} y={height - 8} fill="#64748b" fontSize="10" className="mono">
                Update 1
              </text>
              <text x={padding.left + chartW} y={height - 8} textAnchor="end" fill="#64748b" fontSize="10" className="mono">
                Update {metrics[metrics.length - 1].update}
              </text>
            </>
          )}

          {/* Area Fill */}
          {areaPath1 && <path d={areaPath1} fill="url(#areaGradient)" />}

          {/* Lines */}
          {path1 && <path d={path1} fill="none" stroke={color1} strokeWidth="2.5" strokeLinecap="round" />}
          {path2 && <path d={path2} fill="none" stroke={color2} strokeWidth="1.8" strokeLinecap="round" strokeDasharray="3 3" />}

          {/* Hover hit detection zones */}
          {metrics.map((m, i) => {
            const x = padding.left + (i / Math.max(metrics.length - 1, 1)) * chartW;
            return (
              <rect
                key={i}
                x={x - 10}
                y={padding.top}
                width={20}
                height={chartH}
                fill="transparent"
                style={{ cursor: 'crosshair' }}
                onMouseEnter={() => setHoverPoint(m)}
              />
            );
          })}
        </svg>
      </div>
    </div>
  );
};
