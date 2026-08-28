export interface TankPose {
  x: number;
  y: number;
  angle: number;
  ammo: number;
}

export interface ShellPose {
  x: number;
  y: number;
  angle: number;
  owner: number;
  ttl: number;
}

export interface WallSegment {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface ReplayFrame {
  player: TankPose;
  opponent: TankPose;
  shells: ShellPose[];
  action: [number, number, number]; // [movement, rotation, fire]
  reward: number;
  value: number;
  step?: number;
  update?: number;
  live?: boolean;
}

export interface LiveFrame extends ReplayFrame {
  walls?: WallSegment[];
  dimensions?: {
    width: number;
    height: number;
    cols: number;
    rows: number;
  };
}

export interface ReplayData {
  seed: number;
  total_frames: number;
  total_reward: number;
  winner: 'player' | 'opponent' | 'draw' | 'timeout';
  dimensions: {
    width: number;
    height: number;
    cols: number;
    rows: number;
  };
  walls: WallSegment[];
  frames: ReplayFrame[];
}

export interface ReplayMeta {
  replay_id: string;
  seed: number;
  total_frames: number;
  total_reward: number;
  winner: string;
}
