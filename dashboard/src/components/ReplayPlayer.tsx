import React, { useEffect, useRef, useState } from 'react';
import { LiveFrame, ReplayData, ReplayMeta, WallSegment } from '../types/replay';
import { Play, Pause, RotateCcw, Film, Trophy, ChevronLeft, ChevronRight, Radio, Tv, Zap, Shield, Crosshair } from 'lucide-react';

interface ReplayPlayerProps {
  replays: ReplayMeta[];
  selectedReplay: ReplayData | null;
  liveFrame: LiveFrame | null;
  runStatus?: string;
  onSelectReplay: (replayId: string) => void;
}

export const ReplayPlayer: React.FC<ReplayPlayerProps> = ({
  replays,
  selectedReplay,
  liveFrame,
  runStatus,
  onSelectReplay,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [viewMode, setViewMode] = useState<'live' | 'replay'>(() => (runStatus === 'training' ? 'live' : 'replay'));
  const [currentFrameIdx, setCurrentFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [isLooping, setIsLooping] = useState(true);

  // Auto-switch to live when training begins if requested
  useEffect(() => {
    if (runStatus === 'training' && liveFrame) {
      // User can stay in live or switch to replay
    }
  }, [runStatus, liveFrame]);

  // Playback timer for Replay mode
  useEffect(() => {
    if (viewMode !== 'replay' || !isPlaying || !selectedReplay || selectedReplay.frames.length === 0) return;

    const intervalMs = Math.max(16, Math.floor(50 / playbackSpeed));
    const timer = setInterval(() => {
      setCurrentFrameIdx((prev) => {
        if (prev >= selectedReplay.frames.length - 1) {
          if (isLooping) return 0;
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, intervalMs);

    return () => clearInterval(timer);
  }, [viewMode, isPlaying, playbackSpeed, isLooping, selectedReplay]);

  // Reset frame index on replay change
  useEffect(() => {
    setCurrentFrameIdx(0);
    setIsPlaying(true);
  }, [selectedReplay?.seed, selectedReplay?.total_frames]);

  // Canvas 2D Render Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const isLive = viewMode === 'live' && liveFrame !== null;
    const currentFrame = isLive
      ? liveFrame
      : selectedReplay?.frames[currentFrameIdx] || selectedReplay?.frames[0];

    if (!currentFrame && !selectedReplay && !liveFrame) return;

    const width = (isLive ? liveFrame?.dimensions?.width : selectedReplay?.dimensions?.width) || 660;
    const height = (isLive ? liveFrame?.dimensions?.height : selectedReplay?.dimensions?.height) || 420;
    canvas.width = width;
    canvas.height = height;

    // 1. Clear background with deep tactical aesthetic
    ctx.fillStyle = '#060a14';
    ctx.fillRect(0, 0, width, height);

    // Subtle grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.025)';
    ctx.lineWidth = 1;
    for (let x = 0; x <= width; x += 60) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y <= height; y += 60) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // 2. Draw Maze Walls with crisp neon outline
    const walls: WallSegment[] = (isLive ? liveFrame?.walls : selectedReplay?.walls) || [];
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 4;
    ctx.lineCap = 'round';
    ctx.shadowColor = 'rgba(51, 65, 85, 0.5)';
    ctx.shadowBlur = 4;

    for (const wall of walls) {
      ctx.beginPath();
      ctx.moveTo(wall.x1, wall.y1);
      ctx.lineTo(wall.x2, wall.y2);
      ctx.stroke();
    }
    ctx.shadowBlur = 0;

    if (!currentFrame) return;

    // Helper: Draw Tank (Clean Sprite with no obstructive text labels)
    const drawTank = (
      pose: { x: number; y: number; angle: number; ammo: number; alive?: boolean },
      color: string,
      glowColor: string
    ) => {
      const isAlive = pose.alive !== false;
      ctx.save();
      ctx.translate(pose.x, pose.y);
      ctx.rotate((-pose.angle * Math.PI) / 180);

      // Tank Body (28 x 20) with smooth rounded corners
      ctx.fillStyle = isAlive ? color : '#475569';
      ctx.shadowColor = isAlive ? glowColor : 'transparent';
      ctx.shadowBlur = isAlive ? 10 : 0;
      ctx.beginPath();
      ctx.roundRect(-14, -10, 28, 20, 4);
      ctx.fill();
      ctx.shadowBlur = 0;

      // Tank Tracks (Tactical Dark Gray)
      ctx.fillStyle = '#090d16';
      ctx.fillRect(-14, -13, 28, 4);
      ctx.fillRect(-14, 9, 28, 4);

      // Turret Base (Center Core)
      ctx.fillStyle = '#020617';
      ctx.beginPath();
      ctx.arc(0, 0, 6, 0, Math.PI * 2);
      ctx.fill();

      // Inner Turret Accent
      ctx.fillStyle = isAlive ? glowColor : '#64748b';
      ctx.beginPath();
      ctx.arc(0, 0, 3, 0, Math.PI * 2);
      ctx.fill();

      // Cannon Barrel (Oriented forward in heading direction)
      ctx.fillStyle = isAlive ? color : '#64748b';
      ctx.fillRect(0, -2.5, 17, 5);

      // Barrel tip highlight
      if (isAlive) {
        ctx.fillStyle = glowColor;
        ctx.fillRect(15, -2, 2, 4);
      }

      ctx.restore();
    };

    // 3. Draw Tanks
    if (currentFrame.player) {
      drawTank(currentFrame.player, '#059669', '#34d399');
    }
    if (currentFrame.opponent) {
      drawTank(currentFrame.opponent, '#e11d48', '#fb7185');
    }

    // 4. Draw Shells (Projectiles with glowing particle core)
    if (currentFrame.shells) {
      for (const shell of currentFrame.shells) {
        ctx.save();
        ctx.translate(shell.x, shell.y);

        const shellGlow = shell.owner === 0 ? '#34d399' : '#fb7185';

        // Outer glow
        ctx.fillStyle = shellGlow;
        ctx.shadowColor = shellGlow;
        ctx.shadowBlur = 14;
        ctx.beginPath();
        ctx.arc(0, 0, 4.5, 0, Math.PI * 2);
        ctx.fill();

        // Inner bright white energy core
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(0, 0, 2, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
      }
    }
  }, [viewMode, liveFrame, currentFrameIdx, selectedReplay]);

  const hasReplay = selectedReplay && selectedReplay.frames && selectedReplay.frames.length > 0;
  const isLiveActive = viewMode === 'live' && liveFrame !== null;

  if (!hasReplay && !liveFrame) {
    return (
      <div className="glass-card" style={{ padding: '24px', textAlign: 'center', minHeight: '360px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <Film size={36} color="#64748b" style={{ marginBottom: '12px' }} />
        <div style={{ color: '#94a3b8', fontSize: '1rem', fontWeight: 600 }}>Aguardando Partidas / Replays</div>
        <div style={{ color: '#64748b', fontSize: '0.85rem', marginTop: '4px', maxWidth: '420px' }}>
          O visualizador exibirá a partida em tempo real durante o treinamento e os replays dos checkpoints de avaliação.
        </div>
      </div>
    );
  }

  const currentFrame = isLiveActive
    ? liveFrame
    : selectedReplay?.frames[currentFrameIdx] || selectedReplay?.frames[0];

  const winnerColor = selectedReplay?.winner === 'player' ? '#34d399' : selectedReplay?.winner === 'opponent' ? '#f43f5e' : '#fbbf24';
  const winnerText = selectedReplay?.winner === 'player' ? 'PPO Agent Venceu' : selectedReplay?.winner === 'opponent' ? 'Agent Smith Venceu' : selectedReplay?.winner === 'timeout' ? 'Tempo Esgotado' : 'Empate';

  return (
    <div className="glass-card" style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* 1. Header Toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Tv size={20} color="#38bdf8" />
          <span style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
            Arena 2D de Combate
          </span>

          {/* Mode Switcher */}
          <div style={{ display: 'flex', background: 'rgba(255, 255, 255, 0.05)', borderRadius: '8px', padding: '3px', gap: '4px' }}>
            <button
              onClick={() => setViewMode('live')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 10px',
                borderRadius: '6px',
                border: 'none',
                background: viewMode === 'live' ? 'rgba(244, 63, 94, 0.2)' : 'transparent',
                color: viewMode === 'live' ? '#fb7185' : '#94a3b8',
                fontWeight: viewMode === 'live' ? 700 : 500,
                fontSize: '0.75rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              <Radio size={12} className={runStatus === 'training' ? 'pulse-fast' : ''} />
              <span>AO VIVO</span>
            </button>

            <button
              onClick={() => setViewMode('replay')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 10px',
                borderRadius: '6px',
                border: 'none',
                background: viewMode === 'replay' ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                color: viewMode === 'replay' ? '#38bdf8' : '#94a3b8',
                fontWeight: viewMode === 'replay' ? 700 : 500,
                fontSize: '0.75rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              <Film size={12} />
              <span>REPLAYS GRAVADOS</span>
            </button>
          </div>
        </div>

        {/* Legend / Status Badges */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {/* Legend Tanks */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.75rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#34d399', fontWeight: 600 }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', backgroundColor: '#10b981', display: 'inline-block' }} />
              PPO Agent (Verde)
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#fb7185', fontWeight: 600 }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', backgroundColor: '#f43f5e', display: 'inline-block' }} />
              Agent Smith (Vermelho)
            </span>
          </div>

          {viewMode === 'replay' && selectedReplay && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{
                fontSize: '0.75rem', fontWeight: 700, padding: '2px 8px', borderRadius: '4px',
                backgroundColor: `${winnerColor}20`, color: winnerColor, border: `1px solid ${winnerColor}40`
              }}>
                <Trophy size={11} style={{ display: 'inline', marginRight: '4px' }} />
                {winnerText}
              </span>

              {replays.length > 0 && (
                <select
                  value={replays.find(r => r.replay_id.includes(String(selectedReplay.seed)) || r.total_reward === selectedReplay.total_reward)?.replay_id || replays[0].replay_id}
                  onChange={(e) => onSelectReplay(e.target.value)}
                  style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    borderRadius: '6px',
                    padding: '4px 10px',
                    color: '#f8fafc',
                    fontSize: '0.8rem',
                    outline: 'none',
                    cursor: 'pointer'
                  }}
                >
                  {replays.map((rep) => (
                    <option key={rep.replay_id} value={rep.replay_id} style={{ background: '#0f172a', color: '#f8fafc' }}>
                      {rep.replay_id} • (Reward: {rep.total_reward > 0 ? `+${rep.total_reward}` : rep.total_reward} • {rep.winner})
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}

          {viewMode === 'live' && (
            <span style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '3px 10px',
              borderRadius: '6px',
              backgroundColor: runStatus === 'training' ? 'rgba(244, 63, 94, 0.15)' : 'rgba(56, 189, 248, 0.15)',
              color: runStatus === 'training' ? '#fb7185' : '#38bdf8',
              border: runStatus === 'training' ? '1px solid rgba(244, 63, 94, 0.3)' : '1px solid rgba(56, 189, 248, 0.3)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}>
              <span style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                backgroundColor: runStatus === 'training' ? '#f43f5e' : '#38bdf8',
                display: 'inline-block',
              }} className={runStatus === 'training' ? 'pulse-fast' : ''} />
              {runStatus === 'training' ? 'TRANSMISSÃO AO VIVO • GPU CUDA' : 'ÚLTIMO FRAME DA SESSÃO'}
            </span>
          )}
        </div>
      </div>

      {/* 2. Pure 2D Canvas Arena (Zero obstructing labels on top) */}
      <div style={{
        position: 'relative',
        width: '100%',
        display: 'flex',
        justifyContent: 'center',
        background: '#060a14',
        borderRadius: '10px',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        overflow: 'hidden',
        boxShadow: 'inset 0 0 25px rgba(0, 0, 0, 0.85)'
      }}>
        <canvas
          ref={canvasRef}
          style={{
            maxWidth: '100%',
            height: 'auto',
            display: 'block',
          }}
        />
      </div>

      {/* 3. Dedicated Telemetry & Ammo Bar (Cleanly placed OUTSIDE the game canvas) */}
      {currentFrame && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '10px',
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: '8px',
          padding: '10px 14px',
        }}>
          {/* PPO Agent State */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={15} color="#34d399" />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Munição PPO</span>
              <div style={{ display: 'flex', gap: '3px', marginTop: '2px' }}>
                {[0, 1, 2, 3, 4].map((i) => (
                  <span
                    key={i}
                    style={{
                      width: '12px',
                      height: '5px',
                      borderRadius: '2px',
                      backgroundColor: i < (currentFrame.player?.ammo ?? 5) ? '#34d399' : 'rgba(255,255,255,0.1)',
                    }}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Agent Smith State */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Crosshair size={15} color="#fb7185" />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Munição Smith</span>
              <div style={{ display: 'flex', gap: '3px', marginTop: '2px' }}>
                {[0, 1, 2, 3, 4].map((i) => (
                  <span
                    key={i}
                    style={{
                      width: '12px',
                      height: '5px',
                      borderRadius: '2px',
                      backgroundColor: i < (currentFrame.opponent?.ammo ?? 5) ? '#fb7185' : 'rgba(255,255,255,0.1)',
                    }}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Timing / Step Info */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Shield size={15} color="#38bdf8" />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                {viewMode === 'live' ? 'Update & Passo' : 'Frame do Replay'}
              </span>
              <span className="mono" style={{ fontSize: '0.8rem', color: '#f8fafc', fontWeight: 600 }}>
                {viewMode === 'live'
                  ? `Update #${currentFrame.update || 0} • Passo ${currentFrame.step || 0}`
                  : `Frame ${currentFrameIdx + 1} / ${selectedReplay?.total_frames || 0}`}
              </span>
            </div>
          </div>

          {/* Reward & Value */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '14px' }}>
            <div>
              <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Recompensa: </span>
              <span className="mono" style={{ fontSize: '0.8rem', fontWeight: 700, color: (currentFrame.reward || 0) >= 0 ? '#34d399' : '#fb7185' }}>
                {(currentFrame.reward || 0) > 0 ? `+${currentFrame.reward.toFixed(2)}` : (currentFrame.reward || 0).toFixed(2)}
              </span>
            </div>
            <div>
              <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Critic V(s): </span>
              <span className="mono" style={{ fontSize: '0.8rem', fontWeight: 700, color: '#a78bfa' }}>
                {(currentFrame.value || 0).toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 4. Video Player Controls (Shown only in Replay mode) */}
      {viewMode === 'replay' && selectedReplay && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {/* Timeline Slider */}
          <input
            type="range"
            min={0}
            max={Math.max(0, selectedReplay.total_frames - 1)}
            value={currentFrameIdx}
            onChange={(e) => setCurrentFrameIdx(Number(e.target.value))}
            style={{ width: '100%', cursor: 'pointer' }}
          />

          {/* Buttons Bar */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {/* Step Back */}
              <button
                onClick={() => setCurrentFrameIdx((prev) => Math.max(0, prev - 1))}
                style={{ background: 'rgba(255, 255, 255, 0.05)', border: 'none', borderRadius: '6px', padding: '6px 10px', color: '#94a3b8', cursor: 'pointer' }}
                title="Voltar 1 frame"
              >
                <ChevronLeft size={16} />
              </button>

              {/* Play/Pause */}
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                style={{
                  background: isPlaying ? 'rgba(244, 63, 94, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                  border: isPlaying ? '1px solid rgba(244, 63, 94, 0.4)' : '1px solid rgba(16, 185, 129, 0.4)',
                  borderRadius: '8px',
                  padding: '8px 16px',
                  color: isPlaying ? '#fb7185' : '#34d399',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  cursor: 'pointer'
                }}
              >
                {isPlaying ? <Pause size={16} /> : <Play size={16} />}
                <span>{isPlaying ? 'Pausar' : 'Reproduzir'}</span>
              </button>

              {/* Step Forward */}
              <button
                onClick={() => setCurrentFrameIdx((prev) => Math.min(selectedReplay.total_frames - 1, prev + 1))}
                style={{ background: 'rgba(255, 255, 255, 0.05)', border: 'none', borderRadius: '6px', padding: '6px 10px', color: '#94a3b8', cursor: 'pointer' }}
                title="Avançar 1 frame"
              >
                <ChevronRight size={16} />
              </button>

              {/* Reset / Restart */}
              <button
                onClick={() => setCurrentFrameIdx(0)}
                style={{ background: 'rgba(255, 255, 255, 0.05)', border: 'none', borderRadius: '6px', padding: '6px 10px', color: '#94a3b8', cursor: 'pointer' }}
                title="Reiniciar partida"
              >
                <RotateCcw size={16} />
              </button>
            </div>

            {/* Right: Speed & Loop options */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {/* Speed Selector */}
              <div style={{ display: 'flex', background: 'rgba(255, 255, 255, 0.04)', borderRadius: '6px', padding: '2px' }}>
                {[0.5, 1, 2, 5].map((speed) => (
                  <button
                    key={speed}
                    onClick={() => setPlaybackSpeed(speed)}
                    style={{
                      background: playbackSpeed === speed ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                      color: playbackSpeed === speed ? '#38bdf8' : '#64748b',
                      border: 'none',
                      borderRadius: '4px',
                      padding: '4px 8px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    {speed}x
                  </button>
                ))}
              </div>

              {/* Loop Toggle */}
              <button
                onClick={() => setIsLooping(!isLooping)}
                style={{
                  background: isLooping ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                  color: isLooping ? '#34d399' : '#64748b',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '6px 10px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Loop {isLooping ? 'ON' : 'OFF'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
