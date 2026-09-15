import { useMemo } from 'react';
import { palette } from '../demo/seedData';
import type { BeadColor } from '../types';

export type GridTool = 'select' | 'paint' | 'erase' | 'picker' | 'box' | 'pan';

interface BeadGridProps {
  motif?: 'dog' | 'girl' | 'whale' | 'flower';
  size?: number;
  selected?: Set<number>;
  highlightedColor?: string;
  completed?: Set<number>;
  mirror?: boolean;
  showNumbers?: boolean;
  showOutline?: boolean;
  displayMode?: 'beads' | 'pattern';
  overrides?: Map<number, string | null>;
  cells?: Array<string | null>;
  colors?: BeadColor[];
  onCellClick?: (index: number, color: string | null, event: React.MouseEvent<HTMLButtonElement>) => void;
  onCellHover?: (x: number, y: number, color: string | null) => void;
}

function motifColor(x: number, y: number, size: number, motif: string): string | null {
  const cx = size / 2;
  const cy = size / 2;
  if (motif === 'whale') {
    const body = ((x - cx) ** 2) / (cx * .78) ** 2 + ((y - cy) ** 2) / (cy * .42) ** 2 < 1;
    const tail = x < size * .22 && Math.abs(y - cy) < (size * .3 - x * .5);
    if (!body && !tail) return null;
    if (x > size * .68 && y < cy - 1) return '#F7EEDC';
    return y > cy + 2 ? '#376C84' : '#75AFC0';
  }
  if (motif === 'flower') {
    const d = Math.hypot(x - cx, y - cy);
    const petals = Math.sin(Math.atan2(y - cy, x - cx) * 5) * 2.4;
    if (d < 3) return '#F4C65D';
    if (d < size * .31 + petals) return '#D9827A';
    if (Math.abs(x - cx) < 2 && y > cy) return '#849B70';
    return null;
  }
  if (motif === 'girl') {
    const face = ((x - cx) ** 2) / (cx * .55) ** 2 + ((y - cy) ** 2) / (cy * .7) ** 2 < 1;
    if (!face) return null;
    if (y < size * .32 || x < size * .25 || x > size * .75) return '#376C84';
    if ((x === Math.floor(cx - 3) || x === Math.floor(cx + 3)) && y > cy - 2 && y < cy + 1) return '#30353A';
    if (y > size * .73) return '#75AFC0';
    return '#D9827A';
  }
  const head = ((x - cx) ** 2) / (cx * .55) ** 2 + ((y - cy) ** 2) / (cy * .55) ** 2 < 1;
  const earL = x > size * .18 && x < size * .4 && y > size * .12 && y < size * .4 && y < -x + size * .55;
  const earR = x > size * .6 && x < size * .82 && y > size * .12 && y < size * .4 && y < x - size * .45;
  if (!head && !earL && !earR) return null;
  if ((x === Math.floor(cx - 4) || x === Math.floor(cx + 4)) && y > cy - 2 && y < cy + 1) return '#30353A';
  if (Math.abs(x - cx) < 2 && y > cy + 1 && y < cy + 4) return '#5D382B';
  if (y > cy + 2 && Math.abs(x - cx) < 6) return '#F7EEDC';
  return (x + y) % 4 === 0 ? '#E8874A' : '#9B5B36';
}

export function buildGrid(size = 24, motif = 'dog') {
  return Array.from({ length: size * size }, (_, index) => motifColor(index % size, Math.floor(index / size), size, motif));
}

export function BeadGrid({ motif = 'dog', size = 24, selected = new Set(), highlightedColor, completed = new Set(), mirror, showNumbers, showOutline = false, displayMode = 'beads', overrides = new Map(), cells: providedCells, colors = palette, onCellClick, onCellHover }: BeadGridProps) {
  const cells = useMemo(() => providedCells ?? buildGrid(size, motif), [providedCells, size, motif]);
  const colorCode = (hex: string) => colors.find((item) => item.hex.toLowerCase() === hex.toLowerCase())?.code ?? '';
  const isLight = (hex: string) => {
    const value = hex.replace('#', '');
    const red = parseInt(value.slice(0, 2), 16);
    const green = parseInt(value.slice(2, 4), 16);
    const blue = parseInt(value.slice(4, 6), 16);
    return (red * 299 + green * 587 + blue * 114) / 1000 > 165;
  };
  return (
    <div className={`bead-grid-wrap ${displayMode === 'pattern' ? 'pattern-mode' : 'bead-mode'} ${mirror ? 'is-mirrored' : ''}`}>
      <div className="bead-grid" style={{ '--grid-size': size } as React.CSSProperties}>
        {cells.map((baseColor, index) => {
          const color = overrides.has(index) ? overrides.get(index) ?? null : baseColor;
          const isDimmed = !!highlightedColor && color !== highlightedColor;
          const x = (index % size) + 1;
          const y = Math.floor(index / size) + 1;
          const neighbor = (dx: number, dy: number) => cells[(y - 1 + dy) * size + (x - 1 + dx)];
          const isOutline = Boolean(showOutline && color && ([[-1, 0], [1, 0], [0, -1], [0, 1]] as const).some(([dx, dy]) => {
            const nx = x - 1 + dx;
            const ny = y - 1 + dy;
            return nx < 0 || ny < 0 || nx >= size || ny >= size || !neighbor(dx, dy);
          }));
          return <button
            key={index}
            className={`bead-cell ${color ? 'has-bead' : 'is-empty'} ${color && isLight(color) ? 'is-light-color' : ''} ${selected.has(index) ? 'is-selected' : ''} ${completed.has(index) ? 'is-completed' : ''} ${isDimmed ? 'is-dimmed' : ''} ${isOutline ? 'is-outline' : ''}`}
            style={{ '--bead-color': color ?? 'transparent' } as React.CSSProperties}
            aria-label={`坐标 ${x}, ${y}${color ? `，颜色 ${colorCode(color)}` : '，透明格'}`}
            onClick={(event) => onCellClick?.(index, color, event)}
            onMouseEnter={() => onCellHover?.(x, y, color)}
          >{showNumbers && color ? <span className="bead-code">{colorCode(color)}</span> : null}</button>;
        })}
      </div>
    </div>
  );
}
