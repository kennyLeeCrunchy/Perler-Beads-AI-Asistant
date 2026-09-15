export type WorkStatus = '草稿' | '已完成';

export interface BeadColor {
  brand: 'Mard' | 'Artkal';
  code: string;
  name: string;
  hex: string;
  count: number;
  remaining: number;
}

export interface Work {
  id: string;
  name: string;
  size: '52×52' | '78×78' | '104×104';
  board: string;
  brand: 'Mard' | 'Artkal';
  colors: number;
  beads: number;
  status: WorkStatus;
  createdAt: string;
  updatedAt: string;
  progress: number;
  palette: BeadColor[];
  grid: Array<string | null>;
  gridSize?: number;
  patternId?: string;
  previewDataUrl?: string;
  cleanReferenceId?: string;
  algorithmVersion?: string;
  pipeline?: string;
  mirror?: boolean;
  motif: 'dog' | 'girl' | 'whale' | 'flower';
}
