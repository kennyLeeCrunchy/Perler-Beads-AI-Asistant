import { Check, Search } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { BeadColor } from '../types';

export function ColorSwatch({ color, active, onClick }: { color: BeadColor; active?: boolean; onClick?: () => void }) {
  return <button className={`color-row ${active ? 'is-active' : ''}`} onClick={onClick}>
    <span className="swatch" style={{ background: color.hex }} />
    <span className="color-copy"><strong>{color.code}</strong><small>{color.name}</small></span>
    <span className="color-count">{color.count}<small>颗</small></span>
    {active && <Check size={17} />}
  </button>;
}

export function ColorList({ colors, active, onSelect, showRemaining = false }: { colors: BeadColor[]; active?: string; onSelect?: (color: BeadColor) => void; showRemaining?: boolean }) {
  const [query, setQuery] = useState('');
  const filtered = useMemo(() => colors.filter((color) => `${color.code}${color.name}`.toLowerCase().includes(query.toLowerCase())), [colors, query]);
  return <div className="color-list">
    <label className="search-field"><Search size={17} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="搜索色号或名称" /></label>
    <div className="color-scroll">{filtered.map((color) => showRemaining ? (
      <button key={color.code} className={`remaining-color ${active === color.hex ? 'is-active' : ''}`} onClick={() => onSelect?.(color)}><span className="swatch" style={{ background: color.hex }} /><span><strong>{color.code} · {color.name}</strong><small>剩余 {color.remaining} / {color.count} 颗</small></span></button>
    ) : <ColorSwatch key={color.code} color={color} active={active === color.hex} onClick={() => onSelect?.(color)} />)}</div>
  </div>;
}
