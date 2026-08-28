export interface GpuMetrics {
  device_name: string;
  cuda_available: boolean;
  vram_allocated_mb: number;
  vram_reserved_mb: number;
  vram_total_mb: number;
  vram_percent: number;
  gpu_utilization_percent: number;
  temperature_c: number;
  power_w: number;
}

export interface NeuralActivationSnapshot {
  input_groups: {
    tank_features?: number[];
    shell_sensors?: number[];
    maze_raycasts?: number[];
  };
  hidden_activations: Array<{
    layer: string;
    mean: number;
    max: number;
    sparsity: number;
  }>;
  action_probabilities: {
    movement?: number[]; // [idle, forward, backward]
    rotation?: number[]; // [none, clockwise, counter_clockwise]
    fire?: number[];     // [no, yes]
  };
  predicted_value: number;
}

export interface TrainingProgress {
  status: 'preparing' | 'training' | 'evaluating' | 'paused' | 'completed' | 'error' | 'not_found';
  run_name: string;
  start_time: number;
  elapsed_seconds: number;
  eta_seconds: number;
  current_update: number;
  total_updates: number;
  progress_percent: number;
  total_timesteps: number;
  steps_per_second: number;
  updates_per_second: number;
  mean_reward: number;
  max_reward: number;
  min_reward: number;
  win_rate: number;
  total_episodes: number;
  policy_loss: number;
  value_loss: number;
  entropy: number;
  approx_kl: number;
  clip_fraction: number;
  grad_norm: number;
  learning_rate: number;
  gpu: GpuMetrics;
  neural: NeuralActivationSnapshot;
  latest_metrics: Record<string, any>;
}

export interface MetricPoint {
  update: number;
  mean_reward?: number;
  max_reward?: number;
  min_reward?: number;
  win_rate?: number;
  policy_loss?: number;
  value_loss?: number;
  entropy?: number;
  approx_kl?: number;
  clip_fraction?: number;
  grad_norm?: number;
  learning_rate?: number;
  episodes?: number;
  [key: string]: any;
}

export interface RunSummary {
  run_id: string;
  run_name: string;
  status: string;
  device: string;
  gpu: string;
  current_update: number;
  total_updates: number;
  mean_reward: number;
  win_rate: number;
  elapsed_seconds: number;
  metrics_count: number;
  created_at: string;
}
