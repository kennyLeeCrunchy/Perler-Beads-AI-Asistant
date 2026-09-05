import { Box, Grid3X3, Palette, Sparkles } from 'lucide-react';
import type { Work } from '../types';

export function PatternSummary({ work, compact = false }: { work: Work; compact?: boolean }) {
  const items = [
    { icon: Grid3X3, label: '图纸尺寸', value: work.size },
    { icon: Box, label: '拼豆数量', value: `${work.beads} 颗` },
    { icon: Palette, label: '颜色', value: `${work.colors} 色` },
    { icon: Sparkles, label: '品牌色卡', value: work.brand },
  ];
  return <div className={`pattern-summary ${compact ? 'compact' : ''}`}>{items.map(({ icon: Icon, label, value }) => <div key={label}><Icon size={18} /><span><small>{label}</small><strong>{value}</strong></span></div>)}</div>;
}
