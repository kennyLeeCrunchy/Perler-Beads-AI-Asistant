import { AlertTriangle, CheckCircle2, Crosshair, Flame, Focus, RotateCcw } from 'lucide-react';
import { useState } from 'react';
import type { BeadColor, Work } from '../types';
import { Button } from './Button';
import { ColorList } from './ColorList';

export function MakingAssistantPanel({ work, activeColor, onColor, coordinate, onComplete }: { work: Work; activeColor?: string; onColor: (color: BeadColor) => void; coordinate: string; onComplete: () => void }) {
  const [tab, setTab] = useState<'color' | 'area' | 'iron'>('color');
  return <aside className="making-panel panel-card">
    <div className="panel-tabs"><button className={tab === 'color' ? 'is-active' : ''} onClick={() => setTab('color')}>颜色</button><button className={tab === 'area' ? 'is-active' : ''} onClick={() => setTab('area')}>区域</button><button className={tab === 'iron' ? 'is-active' : ''} onClick={() => setTab('iron')}>熨烫</button></div>
    {tab === 'color' && <><div className="active-helper"><Focus size={20} /><div><small>当前高亮</small><strong>{activeColor ? work.palette.find((c) => c.hex === activeColor)?.code : '选择一个色号'}</strong><span>{activeColor ? `剩余 ${work.palette.find((c) => c.hex === activeColor)?.remaining ?? 0} 颗` : '点击颜色，只看这一种豆子'}</span></div></div><ColorList colors={work.palette} active={activeColor} onSelect={onColor} showRemaining /><Button fullWidth variant="secondary" icon={<CheckCircle2 size={18} />} onClick={onComplete}>标记当前颜色完成</Button></>}
    {tab === 'area' && <div className="assistant-stack"><div className="coordinate-card"><Crosshair /><span><small>当前坐标</small><strong>{coordinate}</strong><em>单板 · {activeColor ? work.palette.find((c) => c.hex === activeColor)?.code : '—'}</em></span></div><div className="metric-row"><div><small>选区尺寸</small><strong>8 × 6</strong></div><div><small>区域豆数</small><strong>34 颗</strong></div></div><div className="tip-card"><Focus /><p><strong>横向连续 8 颗</strong><span>从 X12 到 X19，建议先从边界定位。</span></p></div><Button fullWidth icon={<CheckCircle2 size={18} />} onClick={onComplete}>标记当前区域完成</Button><Button fullWidth variant="ghost" icon={<RotateCcw size={18} />}>重置制作进度</Button></div>}
    {tab === 'iron' && <div className="assistant-stack"><div className="risk-card"><AlertTriangle /><p><strong>边缘结构较细</strong><span>翻面时注意散开，建议先固定外围轮廓。</span></p></div><div className="risk-card"><Flame /><p><strong>分区熨烫建议</strong><span>先固定边缘，再处理中心大色块；均匀施压并等待冷却。</span></p></div><p className="fine-print">此功能提供一般性建议，不代替具体材料说明。</p></div>}
  </aside>;
}
