import React from 'react';
import { GpuMetrics } from '../types/telemetry';
import { Cpu, Zap, Thermometer, HardDrive } from 'lucide-react';

interface GpuMonitorProps {
  gpu: GpuMetrics | undefined;
}

export const GpuMonitor: React.FC<GpuMonitorProps> = ({ gpu }) => {
  const isCuda = gpu?.cuda_available ?? false;
  const vramPercent = isCuda ? (gpu?.vram_percent || 0) : 0;
  const deviceName = isCuda ? (gpu?.device_name || 'Dispositivo CUDA Detectado') : 'Executando em CPU';

  return (
    <div className="glass-card" style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* Title */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Cpu size={18} color="#10b981" />
          <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc' }}>
            Hardware & GPU Monitor
          </span>
        </div>
        <span style={{
          fontSize: '0.75rem', fontWeight: 600, padding: '2px 8px', borderRadius: '4px',
          backgroundColor: isCuda ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
          color: isCuda ? '#34d399' : '#fbbf24',
          border: `1px solid ${isCuda ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`
        }}>
          {isCuda ? 'CUDA 12.6 ATIVO' : 'GPU INATIVA'}
        </span>
      </div>

      {/* GPU Device Name */}
      <div style={{
        background: 'rgba(255, 255, 255, 0.03)',
        border: '1px solid rgba(255, 255, 255, 0.06)',
        borderRadius: '8px',
        padding: '10px 14px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Dispositivo:</span>
        <span className="mono" style={{ fontSize: '0.85rem', fontWeight: 700, color: isCuda ? '#38bdf8' : '#94a3b8' }}>
          {deviceName}
        </span>
      </div>

      {/* VRAM Progress Bar */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.8rem' }}>
          <span style={{ color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <HardDrive size={13} color="#94a3b8" /> VRAM Alocada
          </span>
          <span className="mono" style={{ color: '#f8fafc', fontWeight: 600 }}>
            {isCuda ? `${gpu?.vram_allocated_mb ?? 0} MB / ${gpu?.vram_total_mb ?? 0} MB (${vramPercent}%)` : '0 MB (N/A)'}
          </span>
        </div>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{
              width: `${Math.min(vramPercent, 100)}%`,
              background: vramPercent > 85 ? 'linear-gradient(90deg, #f59e0b, #ef4444)' : 'linear-gradient(90deg, #10b981, #06b6d4)',
              boxShadow: '0 0 10px rgba(16, 185, 129, 0.5)'
            }}
          />
        </div>
      </div>

      {/* Stats Grid: Utilization, Temp, Reserved */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
        <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: '#64748b', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
            <Zap size={11} color="#fbbf24" /> USO GPU
          </div>
          <div className="mono" style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', marginTop: '2px' }}>
            {gpu?.gpu_utilization_percent != null ? `${gpu.gpu_utilization_percent}%` : (isCuda ? 'Ativa' : 'N/A')}
          </div>
        </div>

        <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: '#64748b', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
            <Thermometer size={11} color="#f87171" /> TEMP
          </div>
          <div className="mono" style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', marginTop: '2px' }}>
            {gpu?.temperature_c != null ? `${gpu.temperature_c} °C` : 'N/A'}
          </div>
        </div>

        <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: '#64748b', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
            <HardDrive size={11} color="#a78bfa" /> RESERVADO
          </div>
          <div className="mono" style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', marginTop: '2px' }}>
            {gpu?.vram_reserved_mb ? `${gpu.vram_reserved_mb} MB` : 'N/A'}
          </div>
        </div>
      </div>
    </div>
  );
};
