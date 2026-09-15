import type { CSSProperties, ReactNode } from 'react';

interface CoordinateBoardProps {
  children: ReactNode;
  size?: number;
  mirror?: boolean;
  assist?: boolean;
  guideLabel?: string;
  zoom?: number;
}

export function CoordinateBoard({ children, size = 24, mirror = false, assist = false, guideLabel, zoom = 1 }: CoordinateBoardProps) {
  const numbers = Array.from({ length: size }, (_, index) => mirror ? size - index : index + 1);
  return (
    <div className={`coordinate-board ${assist ? 'assist-board' : ''}`} style={{ '--board-zoom': zoom } as CSSProperties}>
      <span className="axis-corner axis-corner-top-left" />
      <div className="axis axis-horizontal axis-top" style={{ gridTemplateColumns: `repeat(${size}, minmax(0, 1fr))` }}>{numbers.map((number) => <span key={`top-${number}`}>{number}</span>)}</div>
      <span className="axis-corner axis-corner-top-right" />
      <div className="axis axis-vertical axis-left" style={{ gridTemplateRows: `repeat(${size}, minmax(0, 1fr))` }}>{Array.from({ length: size }, (_, index) => <span key={`left-${index}`}>{index + 1}</span>)}</div>
      <div className="coordinate-board-grid">
        {children}
        {assist && <div className="board-guides" aria-hidden="true"><i /><i /><i /><i />{guideLabel && <strong>{guideLabel}</strong>}</div>}
      </div>
      <div className="axis axis-vertical axis-right" style={{ gridTemplateRows: `repeat(${size}, minmax(0, 1fr))` }}>{Array.from({ length: size }, (_, index) => <span key={`right-${index}`}>{index + 1}</span>)}</div>
      <span className="axis-corner axis-corner-bottom-left" />
      <div className="axis axis-horizontal axis-bottom" style={{ gridTemplateColumns: `repeat(${size}, minmax(0, 1fr))` }}>{numbers.map((number) => <span key={`bottom-${number}`}>{number}</span>)}</div>
      <span className="axis-corner axis-corner-bottom-right" />
    </div>
  );
}
