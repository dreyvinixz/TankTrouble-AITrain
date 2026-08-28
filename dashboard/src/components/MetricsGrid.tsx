import React from 'react';
import { TrainingProgress } from '../types/telemetry';
import { Trophy, TrendingUp, Target, BarChart2 } from 'lucide-react';

interface MetricsGridProps {
  telemetry: TrainingProgress | null;
}

export const MetricsGrid: React.FC<MetricsGridProps> = ({ telemetry }) => {
  const currentUpdate = telemetry?.current_update || 0;
  const totalUpdates = telemetry?.total_updates || 0;
  const progressPercent = telemetry?.progress_percent || 0;
  const meanReward = telemetry?.mean_reward || 0;
  const maxReward = telemetry?.max_reward || 0;
  const winRate = telemetry?.win_rate || 0;
  const totalTimesteps = telemetry?.total_timesteps || 0;
  const policyLoss = telemetry?.policy_loss || 0;
  const valueLoss = telemetry?.value_loss || 0;
  const entropy = telemetry?.entropy || 0;
  const approxKl = telemetry?.approx_kl || 0;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '20px' }}>
      {/* 1. Progress Card */}
      <div className="glass-card" style={{ padding: '18px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase' }}>
            Atualizações PPO
          </span>
          <Target size={16} color="#38bdf8" />
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <span className="mono" style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc' }}>
            {currentUpdate}
          </span>
          <span className="mono" style={{ fontSize: '0.9rem', color: '#64748b' }}>
            / {totalUpdates}
          </span>
        </div>
        <div style={{ marginTop: '10px' }}>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{
                width: `${progressPercent}%`,
                background: 'linear-gradient(90deg, #38bdf8, #818cf8)',
                boxShadow: '0 0 8px rgba(56, 189, 248, 0.4)'
              }}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '0.75rem', color: '#64748b' }}>
            <span>{progressPercent}% Concluído</span>
            <span className="mono">{totalTimesteps.toLocaleString()} steps</span>
          </div>
        </div>
      </div>

      {/* 2. Reward Card */}
      <div className="glass-card" style={{ padding: '18px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase' }}>
            Recompensa Média
          </span>
          <TrendingUp size={16} color="#34d399" />
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <span className="mono" style={{ fontSize: '1.75rem', fontWeight: 800, color: meanReward >= 0 ? '#34d399' : '#f87171' }}>
            {meanReward > 0 ? `+${meanReward.toFixed(2)}` : meanReward.toFixed(2)}
          </span>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>/ ep</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '14px', fontSize: '0.8rem' }}>
          <span style={{ color: '#64748b' }}>Melhor Reward:</span>
          <span className="mono" style={{ color: '#f8fafc', fontWeight: 700 }}>
            {maxReward > 0 ? `+${maxReward.toFixed(2)}` : maxReward.toFixed(2)}
          </span>
        </div>
      </div>

      {/* 3. Win Rate vs Agent Smith */}
      <div className="glass-card" style={{ padding: '18px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase' }}>
            Win Rate vs Baseline
          </span>
          <Trophy size={16} color="#fbbf24" />
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <span className="mono" style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fbbf24' }}>
            {(winRate * 100).toFixed(1)}%
          </span>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>vitórias</span>
        </div>
        <div style={{ marginTop: '10px' }}>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{
                width: `${Math.min(winRate * 100, 100)}%`,
                background: 'linear-gradient(90deg, #f59e0b, #10b981)',
                boxShadow: '0 0 8px rgba(245, 158, 11, 0.4)'
              }}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '0.75rem', color: '#64748b' }}>
            <span>Oponente: Agent Smith</span>
            <span className="mono">{telemetry?.total_episodes || 0} eps</span>
          </div>
        </div>
      </div>

      {/* 4. Loss & Entropy Overview */}
      <div className="glass-card" style={{ padding: '18px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase' }}>
            Otimizador PPO
          </span>
          <BarChart2 size={16} color="#a78bfa" />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '4px' }}>
          <div>
            <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Policy Loss</div>
            <div className="mono" style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>
              {policyLoss.toFixed(4)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Value Loss</div>
            <div className="mono" style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>
              {valueLoss.toFixed(4)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Entropia</div>
            <div className="mono" style={{ fontSize: '0.95rem', fontWeight: 700, color: '#a78bfa' }}>
              {entropy.toFixed(3)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Approx KL</div>
            <div className="mono" style={{ fontSize: '0.95rem', fontWeight: 700, color: '#38bdf8' }}>
              {approxKl.toFixed(5)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
