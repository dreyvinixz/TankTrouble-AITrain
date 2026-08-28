import React from 'react';
import { NeuralActivationSnapshot } from '../types/telemetry';
import { Network, Zap, Shield, Crosshair, ArrowRight, Gauge, Activity } from 'lucide-react';

interface NeuralInspectorProps {
  neural: NeuralActivationSnapshot | undefined;
}

export const NeuralInspector: React.FC<NeuralInspectorProps> = ({ neural }) => {
  const movementProbs = neural?.action_probabilities?.movement || [0.33, 0.33, 0.34];
  const rotationProbs = neural?.action_probabilities?.rotation || [0.33, 0.33, 0.34];
  const fireProbs = neural?.action_probabilities?.fire || [0.8, 0.2];
  const valueEstimate = neural?.predicted_value ?? 0.0;
  const hiddenLayers = neural?.hidden_activations || [];

  const movementLabels = ['Parado', 'Avançar (Frente)', 'Recuar (Ré)'];
  const rotationLabels = ['Sem Giro', 'Giro Horário (CW)', 'Giro Anti-horário (CCW)'];
  const fireLabels = ['Aguardar', 'DISPARAR PROJÉTIL'];

  const getBestIndex = (arr: number[]) => {
    let best = 0;
    for (let i = 1; i < arr.length; i++) {
      if (arr[i] > arr[best]) best = i;
    }
    return best;
  };

  const bestMove = getBestIndex(movementProbs);
  const bestRotate = getBestIndex(rotationProbs);
  const bestFire = getBestIndex(fireProbs);

  return (
    <div className="glass-card" style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Title */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Network size={18} color="#a78bfa" />
          <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>
            Inspetor da Rede Neural (Actor-Critic)
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: '#a78bfa' }}>
          <Gauge size={13} />
          <span>V(s) Estimado: </span>
          <span className="mono" style={{ fontWeight: 700, color: valueEstimate >= 0 ? '#34d399' : '#f87171' }}>
            {valueEstimate > 0 ? `+${valueEstimate.toFixed(3)}` : valueEstimate.toFixed(3)}
          </span>
        </div>
      </div>

      {/* Architecture Pipeline Flow */}
      <div style={{
        background: 'rgba(255, 255, 255, 0.02)',
        border: '1px solid rgba(255, 255, 255, 0.06)',
        borderRadius: '10px',
        padding: '12px 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '8px'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase' }}>384 Entradas</div>
          <div className="mono" style={{ fontSize: '0.85rem', fontWeight: 700, color: '#38bdf8' }}>12T + 56S + 308M + 8L</div>
        </div>

        <ArrowRight size={14} color="#64748b" />

        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase' }}>Oculta 1</div>
          <div className="mono" style={{ fontSize: '0.85rem', fontWeight: 700, color: '#a78bfa' }}>256 (Tanh)</div>
        </div>

        <ArrowRight size={14} color="#64748b" />

        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase' }}>Oculta 2</div>
          <div className="mono" style={{ fontSize: '0.85rem', fontWeight: 700, color: '#a78bfa' }}>256 (Tanh)</div>
        </div>

        <ArrowRight size={14} color="#64748b" />

        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase' }}>Actor Heads</div>
          <div className="mono" style={{ fontSize: '0.85rem', fontWeight: 700, color: '#34d399' }}>3 Mov • 3 Rot • 2 Fire</div>
        </div>
      </div>

      {/* Input Group Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
        <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '10px', borderRadius: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', color: '#38bdf8', marginBottom: '4px' }}>
            <Shield size={12} /> Tanques (12)
          </div>
          <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Posição, ângulo, munição e distância</div>
        </div>

        <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '10px', borderRadius: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', color: '#f43f5e', marginBottom: '4px' }}>
            <Crosshair size={12} /> Projéteis (56)
          </div>
          <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>8 tiros mais próximos, ângulos e owner</div>
        </div>

        <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '10px', borderRadius: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', color: '#34d399', marginBottom: '4px' }}>
            <Zap size={12} /> Topologia (308)
          </div>
          <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>77 células x 4 paredes N/E/S/W</div>
        </div>

        <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '10px', borderRadius: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', color: '#fbbf24', marginBottom: '4px' }}>
            <Network size={12} /> Lidar 360° (8)
          </div>
          <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>8 raios egocêntricos (Frente, Lados, Trás)</div>
        </div>
      </div>

      {/* Real Hidden Layer Neuron Activation Grid */}
      {hiddenLayers.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', background: 'rgba(255, 255, 255, 0.02)', padding: '12px', borderRadius: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem', color: '#a78bfa' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Activity size={12} /> Ativações Ocultas Amostradas (256 Neurônios)
            </span>
            <span>Esparsidade: {((hiddenLayers[0]?.sparsity ?? 0.5) * 100).toFixed(0)}%</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {hiddenLayers.map((layer, lIdx) => (
              <div key={lIdx} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.7rem', color: '#64748b', minWidth: '55px' }}>{layer.layer}:</span>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(16, 1fr)', gap: '3px', flex: 1 }}>
                  {(layer.sample_neurons || []).map((val: number, nIdx: number) => {
                    const intensity = Math.min(Math.max((val + 1) / 2, 0), 1);
                    return (
                      <div
                        key={nIdx}
                        title={`Neurônio ${nIdx * 16}: ${val.toFixed(3)}`}
                        style={{
                          height: '14px',
                          borderRadius: '2px',
                          backgroundColor: val >= 0
                            ? `rgba(139, 92, 246, ${Math.max(0.15, intensity)})`
                            : `rgba(244, 63, 94, ${Math.max(0.15, 1 - intensity)})`,
                          border: '1px solid rgba(255, 255, 255, 0.05)',
                        }}
                      />
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Probability Bars */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '4px' }}>
        {/* Movement */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '6px' }}>
            <span>Decisão de Movimento (Translação)</span>
            <span className="mono" style={{ color: '#34d399', fontWeight: 600 }}>{movementLabels[bestMove]}</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
            {movementProbs.map((prob, i) => (
              <div key={i} style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px 8px', borderRadius: '6px', border: i === bestMove ? '1px solid rgba(52, 211, 153, 0.4)' : '1px solid transparent' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#64748b' }}>
                  <span>{movementLabels[i]}</span>
                  <span className="mono" style={{ color: i === bestMove ? '#34d399' : '#94a3b8' }}>{(prob * 100).toFixed(1)}%</span>
                </div>
                <div className="progress-bar" style={{ marginTop: '4px', height: '4px' }}>
                  <div className="progress-fill" style={{ width: `${prob * 100}%`, background: i === bestMove ? '#34d399' : '#64748b' }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Rotation */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '6px' }}>
            <span>Decisão de Rotação (Giro da Torre)</span>
            <span className="mono" style={{ color: '#38bdf8', fontWeight: 600 }}>{rotationLabels[bestRotate]}</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
            {rotationProbs.map((prob, i) => (
              <div key={i} style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px 8px', borderRadius: '6px', border: i === bestRotate ? '1px solid rgba(56, 189, 248, 0.4)' : '1px solid transparent' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#64748b' }}>
                  <span>{rotationLabels[i]}</span>
                  <span className="mono" style={{ color: i === bestRotate ? '#38bdf8' : '#94a3b8' }}>{(prob * 100).toFixed(1)}%</span>
                </div>
                <div className="progress-bar" style={{ marginTop: '4px', height: '4px' }}>
                  <div className="progress-fill" style={{ width: `${prob * 100}%`, background: i === bestRotate ? '#38bdf8' : '#64748b' }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Fire */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '6px' }}>
            <span>Decisão de Disparo de Projétil</span>
            <span className="mono" style={{ color: bestFire === 1 ? '#fb7185' : '#94a3b8', fontWeight: 600 }}>{fireLabels[bestFire]}</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px' }}>
            {fireProbs.map((prob, i) => (
              <div key={i} style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px 8px', borderRadius: '6px', border: i === bestFire ? (i === 1 ? '1px solid rgba(244, 63, 94, 0.4)' : '1px solid rgba(255,255,255,0.2)') : '1px solid transparent' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#64748b' }}>
                  <span>{fireLabels[i]}</span>
                  <span className="mono" style={{ color: i === bestFire && i === 1 ? '#fb7185' : '#94a3b8' }}>{(prob * 100).toFixed(1)}%</span>
                </div>
                <div className="progress-bar" style={{ marginTop: '4px', height: '4px' }}>
                  <div className="progress-fill" style={{ width: `${prob * 100}%`, background: i === 1 ? '#f43f5e' : '#64748b' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
