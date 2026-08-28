import React, { useEffect, useRef, useState } from 'react';
import { ReplayData, ReplayMeta } from '../types/replay';
import { Play, Pause, RotateCcw, Film, Trophy, ChevronLeft, ChevronRight } from 'lucide-react';

interface ReplayPlayerProps {
  replays: ReplayMeta[];
  selectedReplay: ReplayData | null;
  onSelectReplay: (replayId: string) => void;
}

export const ReplayPlayer: React.FC<ReplayPlayerProps> = ({
  replays,
  selectedReplay,
  onSelectReplay,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [currentFrameIdx, setCurrentFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [isLooping, setIsLooping] = useState(true);

  // Playback timer
  useEffect(() => {
    if (!isPlaying || !selectedReplay || selectedReplay.frames.length === 0) return;

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
  }, [isPlaying, playbackSpeed, isLooping, selectedReplay]);

  // Reset frame index on replay change
  useEffect(() => {
    setCurrentFrameIdx(0);
    setIsPlaying(true);
  }, [selectedReplay?.seed, selectedReplay?.total_frames]);

  // Canvas 2D Render Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !selectedReplay) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = selectedReplay.dimensions?.width || 660;
    const height = selectedReplay.dimensions?.height || 420;
    canvas.width = width;
    canvas.height = height;

    const frame = selectedReplay.frames[currentFrameIdx] || selectedReplay.frames[0];
    if (!frame) return;

    // 1. Clear background & draw subtle grid
    ctx.fillStyle = '#0b1120';
    ctx.fillRect(0, 0, width, height);

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
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

    // 2. Draw Maze Walls
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 4;
    ctx.lineCap = 'round';
    ctx.shadowColor = 'rgba(71, 85, 105, 0.6)';
    ctx.shadowBlur = 6;

    for (const wall of selectedReplay.walls) {
      ctx.beginPath();
      ctx.moveTo(wall.x1, wall.y1);
      ctx.lineTo(wall.x2, wall.y2);
      ctx.stroke();
    }
    ctx.shadowBlur = 0;

    // Helper: Draw Tank
    const drawTank = (pose: { x: number; y: number; angle: number; ammo: number; alive?: boolean }, color: string, label: string) => {
      const isAlive = pose.alive !== false;
      ctx.save();
      ctx.translate(pose.x, pose.y);
      // In TankArena, nextX = x + cos(rad), nextY = y - sin(rad)
      ctx.rotate((-pose.angle * Math.PI) / 180);

      // Tank Body (28 x 20)
      ctx.fillStyle = isAlive ? color : '#64748b';
      ctx.shadowColor = isAlive ? color : 'transparent';
      ctx.shadowBlur = isAlive ? 8 : 0;
      ctx.beginPath();
      ctx.roundRect(-14, -10, 28, 20, 4);
      ctx.fill();
      ctx.shadowBlur = 0;

      // Tank Tracks
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(-14, -13, 28, 4);
      ctx.fillRect(-14, 9, 28, 4);

      // Turret Base
      ctx.fillStyle = '#020617';
      ctx.beginPath();
      ctx.arc(0, 0, 6, 0, Math.PI * 2);
      ctx.fill();

      // Cannon Barrel (pointing forward in heading direction)
      ctx.fillStyle = isAlive ? color : '#64748b';
      ctx.fillRect(0, -2.5, 17, 5);

      ctx.restore();

      // Tank Label & Ammo above tank
      ctx.save();
      ctx.fillStyle = isAlive ? '#f8fafc' : '#94a3b8';
      ctx.font = 'bold 10px Outfit, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(isAlive ? label : `${label} (Destruído)`, pose.x, pose.y - 18);

      // Ammo pips
      if (isAlive) {
        for (let a = 0; a < 5; a++) {
          ctx.fillStyle = a < pose.ammo ? color : 'rgba(255, 255, 255, 0.2)';
          ctx.fillRect(pose.x - 12 + a * 5, pose.y - 14, 3, 3);
        }
      }
      ctx.restore();
    };

    // 3. Draw Player Tank (Green) & Opponent Tank (Red)
    drawTank(frame.player, '#10b981', 'PPO Agent');
    drawTank(frame.opponent, '#f43f5e', 'Agent Smith');

    // 4. Draw Shells (Bouncing Projectiles with glow trails)
    // First draw motion trails from past 3 frames
    const trailFrames = selectedReplay.frames.slice(Math.max(0, currentFrameIdx - 3), currentFrameIdx);
    for (let tIdx = 0; tIdx < trailFrames.length; tIdx++) {
      const pastFrame = trailFrames[tIdx];
      const opacity = (tIdx + 1) / (trailFrames.length + 1) * 0.4;
      for (const pastShell of pastFrame.shells) {
        ctx.fillStyle = pastShell.owner === 0 ? `rgba(52, 211, 153, ${opacity})` : `rgba(251, 113, 133, ${opacity})`;
        ctx.beginPath();
        ctx.arc(pastShell.x, pastShell.y, 2.5, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Now draw active shells for current frame
    for (const shell of frame.shells) {
      ctx.save();
      ctx.translate(shell.x, shell.y);

      const shellColor = shell.owner === 0 ? '#34d399' : '#fb7185';
      ctx.fillStyle = shellColor;
      ctx.shadowColor = shellColor;
      ctx.shadowBlur = 12;
      ctx.beginPath();
      ctx.arc(0, 0, 4, 0, Math.PI * 2);
      ctx.fill();

      // Inner bright core
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(0, 0, 2, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();
    }
  }, [currentFrameIdx, selectedReplay]);

  if (!selectedReplay || selectedReplay.frames.length === 0) {
    return (
      <div className="glass-card" style={{ padding: '24px', textAlign: 'center', minHeight: '360px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <Film size={36} color="#64748b" style={{ marginBottom: '12px' }} />
        <div style={{ color: '#94a3b8', fontSize: '1rem', fontWeight: 600 }}>Nenhum Replay Disponível</div>
        <div style={{ color: '#64748b', fontSize: '0.85rem', marginTop: '4px', maxWidth: '400px' }}>
          Os replays das partidas determinísticas de avaliação são gravados automaticamente nos checkpoints periódicos.
        </div>
      </div>
    );
  }

  const currentFrame = selectedReplay.frames[currentFrameIdx] || selectedReplay.frames[0];
  const winnerColor = selectedReplay.winner === 'player' ? '#34d399' : selectedReplay.winner === 'opponent' ? '#f43f5e' : '#fbbf24';
  const winnerText = selectedReplay.winner === 'player' ? 'PPO Agent Venceu' : selectedReplay.winner === 'opponent' ? 'Agent Smith Venceu' : selectedReplay.winner === 'timeout' ? 'Tempo Esgotado' : 'Empate';

  return (
    <div className="glass-card" style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Replay Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Film size={20} color="#10b981" />
          <span style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
            Replay da Arena 2D
          </span>
          <span style={{
            fontSize: '0.75rem', fontWeight: 700, padding: '2px 8px', borderRadius: '4px',
            backgroundColor: `${winnerColor}20`, color: winnerColor, border: `1px solid ${winnerColor}40`
          }}>
            <Trophy size={11} style={{ display: 'inline', marginRight: '4px' }} />
            {winnerText}
          </span>
        </div>

        {/* Replay Selector Dropdown */}
        {replays.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Partida:</span>
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
          </div>
        )}
      </div>

      {/* 2D Canvas Arena Container */}
      <div style={{
        position: 'relative',
        width: '100%',
        display: 'flex',
        justifyContent: 'center',
        background: '#040711',
        borderRadius: '12px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        overflow: 'hidden',
        boxShadow: 'inset 0 0 30px rgba(0, 0, 0, 0.8)'
      }}>
        <canvas
          ref={canvasRef}
          style={{
            maxWidth: '100%',
            height: 'auto',
            display: 'block',
          }}
        />

        {/* In-game HUD Overlay */}
        <div style={{
          position: 'absolute',
          top: '12px',
          left: '16px',
          right: '16px',
          display: 'flex',
          justifyContent: 'space-between',
          pointerEvents: 'none'
        }}>
          <div style={{ background: 'rgba(11, 17, 32, 0.85)', backdropFilter: 'blur(8px)', padding: '6px 12px', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.75rem' }}>
            <span style={{ color: '#94a3b8' }}>Frame: </span>
            <span className="mono" style={{ color: '#38bdf8', fontWeight: 700 }}>{currentFrameIdx + 1}</span>
            <span style={{ color: '#64748b' }}> / {selectedReplay.total_frames}</span>
          </div>

          <div style={{ background: 'rgba(11, 17, 32, 0.85)', backdropFilter: 'blur(8px)', padding: '6px 12px', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.75rem', display: 'flex', gap: '12px' }}>
            <div>
              <span style={{ color: '#94a3b8' }}>Step Reward: </span>
              <span className="mono" style={{ color: currentFrame.reward >= 0 ? '#34d399' : '#f87171', fontWeight: 700 }}>
                {currentFrame.reward > 0 ? `+${currentFrame.reward.toFixed(2)}` : currentFrame.reward.toFixed(2)}
              </span>
            </div>
            <div>
              <span style={{ color: '#94a3b8' }}>Critic V(s): </span>
              <span className="mono" style={{ color: '#a78bfa', fontWeight: 700 }}>{currentFrame.value?.toFixed(2) || '0.00'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Video Player Controls */}
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
    </div>
  );
};
