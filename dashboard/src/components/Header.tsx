import React from 'react';
import { RunSummary, TrainingProgress } from '../types/telemetry';
import { Activity, Clock, Play, CheckCircle2, AlertTriangle, Layers } from 'lucide-react';

interface HeaderProps {
  runs: RunSummary[];
  selectedRunId: string;
  onSelectRun: (runId: string) => void;
  telemetry: TrainingProgress | null;
  isConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  runs,
  selectedRunId,
  onSelectRun,
  telemetry,
  isConnected,
}) => {
  const status = telemetry?.status || 'preparing';

  const formatTime = (seconds: number) => {
    if (!seconds || isNaN(seconds) || seconds < 0) return '00:00:00';
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hrs.toString().padStart(2, '0')}h:${mins.toString().padStart(2, '0')}m:${secs.toString().padStart(2, '0')}s`;
  };

  const getStatusBadge = () => {
    switch (status) {
      case 'training':
        return (
          <span className="badge badge-training">
            <span className="pulse-dot" style={{ backgroundColor: '#10b981' }} />
            Treinando PPO
          </span>
        );
      case 'completed':
        return (
          <span className="badge badge-completed">
            <CheckCircle2 size={13} />
            Concluído
          </span>
        );
      case 'error':
        return (
          <span className="badge badge-error">
            <AlertTriangle size={13} />
            Erro
          </span>
        );
      case 'paused':
        return (
          <span className="badge badge-paused">
            <Clock size={13} />
            Pausado
          </span>
        );
      default:
        return (
          <span className="badge badge-training" style={{ opacity: 0.7 }}>
            <Activity size={13} />
            Preparando
          </span>
        );
    }
  };

  return (
    <header className="glass-card" style={{ padding: '16px 24px', marginBottom: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        {/* Left: Brand & Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '42px', height: '42px', borderRadius: '12px',
            background: 'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 20px rgba(16, 185, 129, 0.4)'
          }}>
            <Play size={22} color="#ffffff" fill="#ffffff" style={{ marginLeft: '2px' }} />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{ fontSize: '1.25rem', fontWeight: '800', letterSpacing: '-0.02em', background: 'linear-gradient(90deg, #f8fafc, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                TankTrouble AI Train
              </h1>
              {getStatusBadge()}
              <span title={isConnected ? 'WebSocket Conectado' : 'Reconectando...'} style={{
                width: '8px', height: '8px', borderRadius: '50%',
                backgroundColor: isConnected ? '#10b981' : '#f59e0b',
                boxShadow: isConnected ? '0 0 8px #10b981' : '0 0 8px #f59e0b'
              }} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '2px', fontSize: '0.85rem', color: '#94a3b8' }}>
              <span>CUDA PPO Benchmark</span>
              <span>•</span>
              <span>Target: Agent Smith Baseline</span>
            </div>
          </div>
        </div>

        {/* Center: Run Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Layers size={16} color="#94a3b8" />
          <select
            value={selectedRunId}
            onChange={(e) => onSelectRun(e.target.value)}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '8px',
              padding: '6px 12px',
              color: '#f8fafc',
              fontFamily: 'inherit',
              fontSize: '0.85rem',
              outline: 'none',
              cursor: 'pointer',
              minWidth: '220px'
            }}
          >
            {runs.length === 0 ? (
              <option value="">Nenhuma run encontrada</option>
            ) : (
              runs.map((r) => (
                <option key={r.run_id} value={r.run_id} style={{ background: '#0f172a', color: '#f8fafc' }}>
                  {r.run_name} ({r.current_update}/{r.total_updates})
                </option>
              ))
            )}
          </select>
        </div>

        {/* Right: Quick Telemetry Counters */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
              Tempo Treinando
            </div>
            <div className="mono" style={{ fontSize: '1rem', fontWeight: 700, color: '#38bdf8' }}>
              {formatTime(telemetry?.elapsed_seconds || 0)}
            </div>
          </div>

          <div style={{ width: '1px', height: '28px', background: 'rgba(255, 255, 255, 0.1)' }} />

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
              ETA Restante
            </div>
            <div className="mono" style={{ fontSize: '1rem', fontWeight: 700, color: '#a78bfa' }}>
              {telemetry?.status === 'completed' ? 'Concluído' : formatTime(telemetry?.eta_seconds || 0)}
            </div>
          </div>

          <div style={{ width: '1px', height: '28px', background: 'rgba(255, 255, 255, 0.1)' }} />

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
              Velocidade
            </div>
            <div className="mono" style={{ fontSize: '1rem', fontWeight: 700, color: '#34d399' }}>
              {(telemetry?.steps_per_second || 0).toLocaleString()} <span style={{ fontSize: '0.75rem', color: '#64748b' }}>steps/s</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
