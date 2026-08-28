import { MetricPoint, RunSummary, TrainingProgress } from '../types/telemetry';
import { ReplayData, ReplayMeta } from '../types/replay';

const API_BASE = '/api';

export async function fetchRuns(): Promise<RunSummary[]> {
  const res = await fetch(`${API_BASE}/runs`);
  if (!res.ok) throw new Error('Falha ao carregar lista de execuções');
  return res.json();
}

export async function fetchRunState(runId: string): Promise<TrainingProgress> {
  const res = await fetch(`${API_BASE}/runs/${runId}/state`);
  if (!res.ok) throw new Error(`Falha ao obter estado da run ${runId}`);
  return res.json();
}

export async function fetchRunMetrics(runId: string, limit = 5000): Promise<MetricPoint[]> {
  const res = await fetch(`${API_BASE}/runs/${runId}/metrics?limit=${limit}`);
  if (!res.ok) throw new Error(`Falha ao obter métricas da run ${runId}`);
  return res.json();
}

export async function fetchRunReplays(runId: string): Promise<ReplayMeta[]> {
  const res = await fetch(`${API_BASE}/runs/${runId}/replays`);
  if (!res.ok) return [];
  return res.json();
}

export async function fetchReplayData(runId: string, replayId: string): Promise<ReplayData> {
  const res = await fetch(`${API_BASE}/runs/${runId}/replays/${replayId}`);
  if (!res.ok) throw new Error(`Falha ao carregar dados do replay ${replayId}`);
  return res.json();
}

export function createLiveTelemetrySocket(
  runId: string,
  onMessage: (data: TrainingProgress) => void,
  onError?: (err: Event) => void
): () => void {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/live/${runId}`;
  let socket: WebSocket | null = null;
  let closedManually = false;
  let reconnectTimeout: any = null;

  function connect() {
    if (closedManually) return;
    socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'telemetry' && payload.data) {
          onMessage(payload.data);
        }
      } catch (err) {
        console.error('Erro ao processar pacote WebSocket:', err);
      }
    };

    socket.onerror = (err) => {
      if (onError) onError(err);
    };

    socket.onclose = () => {
      if (!closedManually) {
        reconnectTimeout = setTimeout(connect, 2000);
      }
    };
  }

  connect();

  return () => {
    closedManually = true;
    if (reconnectTimeout) clearTimeout(reconnectTimeout);
    if (socket) socket.close();
  };
}
