import React, { useEffect, useState } from 'react';
import { MetricPoint, RunSummary, TrainingProgress } from './types/telemetry';
import { ReplayData, ReplayMeta } from './types/replay';
import {
  createLiveTelemetrySocket,
  fetchReplayData,
  fetchRunMetrics,
  fetchRunReplays,
  fetchRuns,
  fetchRunState,
} from './services/api';
import { Header } from './components/Header';
import { MetricsGrid } from './components/MetricsGrid';
import { ChartsPanel } from './components/ChartsPanel';
import { GpuMonitor } from './components/GpuMonitor';
import { NeuralInspector } from './components/NeuralInspector';
import { ReplayPlayer } from './components/ReplayPlayer';

export const App: React.FC = () => {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const [telemetry, setTelemetry] = useState<TrainingProgress | null>(null);
  const [metrics, setMetrics] = useState<MetricPoint[]>([]);
  const [replays, setReplays] = useState<ReplayMeta[]>([]);
  const [selectedReplay, setSelectedReplay] = useState<ReplayData | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);

  // 1. Initial load of runs list
  useEffect(() => {
    async function loadRuns() {
      try {
        const fetchedRuns = await fetchRuns();
        setRuns(fetchedRuns);
        if (fetchedRuns.length > 0 && !selectedRunId) {
          setSelectedRunId(fetchedRuns[0].run_id);
        }
      } catch (err) {
        console.error('Erro ao carregar runs:', err);
      }
    }
    loadRuns();
    const interval = setInterval(loadRuns, 5000);
    return () => clearInterval(interval);
  }, []);

  // 2. Load run state, metrics, and replays when selectedRunId changes
  useEffect(() => {
    if (!selectedRunId) return;

    async function loadRunData() {
      try {
        const [stateData, metricsData, replaysData] = await Promise.all([
          fetchRunState(selectedRunId),
          fetchRunMetrics(selectedRunId),
          fetchRunReplays(selectedRunId),
        ]);

        setTelemetry(stateData);
        setMetrics(metricsData);
        setReplays(replaysData);

        // Load latest/best replay if available
        if (replaysData.length > 0) {
          const replayContent = await fetchReplayData(selectedRunId, replaysData[0].replay_id);
          setSelectedReplay(replayContent);
        } else {
          setSelectedReplay(null);
        }
      } catch (err) {
        console.error('Erro ao carregar dados da run selecionada:', err);
      }
    }

    loadRunData();

    // 3. Connect WebSocket for live streaming
    const cleanupWs = createLiveTelemetrySocket(
      selectedRunId,
      (liveTelemetry) => {
        setIsConnected(true);
        setTelemetry(liveTelemetry);

        // Append latest metric point to charts if available
        if (liveTelemetry.latest_metrics && liveTelemetry.latest_metrics.update) {
          setMetrics((prev) => {
            const lastUpdate = prev.length > 0 ? prev[prev.length - 1].update : 0;
            if (liveTelemetry.latest_metrics.update > lastUpdate) {
              return [...prev, liveTelemetry.latest_metrics as MetricPoint];
            }
            return prev;
          });
        }
      },
      () => setIsConnected(false)
    );

    return () => {
      cleanupWs();
      setIsConnected(false);
    };
  }, [selectedRunId]);

  const handleSelectReplay = async (replayId: string) => {
    if (!selectedRunId || !replayId) return;
    try {
      const data = await fetchReplayData(selectedRunId, replayId);
      setSelectedReplay(data);
    } catch (err) {
      console.error('Erro ao carregar replay específico:', err);
    }
  };

  return (
    <div style={{ maxWidth: '1600px', margin: '0 auto', padding: '24px 20px' }}>
      {/* 1. Header & Quick Counters */}
      <Header
        runs={runs}
        selectedRunId={selectedRunId}
        onSelectRun={setSelectedRunId}
        telemetry={telemetry}
        isConnected={isConnected}
      />

      {/* 2. Main KPI Metrics Grid */}
      <MetricsGrid telemetry={telemetry} />

      {/* 3. Two-Column Dashboard Layout */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1.4fr) minmax(0, 1fr)',
          gap: '20px',
          alignItems: 'start',
        }}
      >
        {/* Left Column: Charts & 2D Replay Player */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <ChartsPanel metrics={metrics} />
          <ReplayPlayer
            replays={replays}
            selectedReplay={selectedReplay}
            onSelectReplay={handleSelectReplay}
          />
        </div>

        {/* Right Column: Hardware GPU Monitor & Neural Network Inspector */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <GpuMonitor gpu={telemetry?.gpu} />
          <NeuralInspector neural={telemetry?.neural} />
        </div>
      </div>

      {/* Footer */}
      <footer
        style={{
          marginTop: '32px',
          padding: '16px 0',
          borderTop: '1px solid rgba(255, 255, 255, 0.05)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.8rem',
          color: '#64748b',
        }}
      >
        <div>TankTrouble AI Train • PPO Baseline vs Agent Smith</div>
        <div className="mono">CUDA 12.6 • PyTorch • pybind11 • React + Vite</div>
      </footer>
    </div>
  );
};
