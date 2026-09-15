import { AlertTriangle, CheckCircle2, Crosshair, Flame, Focus, RotateCcw } from 'lucide-react';
import { useState } from 'react';
import type { BeadColor, Work } from '../types';
import { Button } from './Button';
import { ColorList } from './ColorList';
import { buildGrid } from './BeadGrid';

export function MakingAssistantPanel({ work, activeColor, onColor, coordinate, onComplete, onReset }: { work: Work; activeColor?: string; onColor: (color: BeadColor) => void; coordinate: string; onComplete: () => void; onReset: () => void }) {
  const [tab, setTab] = useState<'color' | 'area' | 'iron'>('color');
  const size = work.gridSize ?? 24;
  const cells = work.grid.length === size * size ? work.grid : buildGrid(size, work.motif);
  const filled = cells.filter(Boolean).length;
  const currentCount = activeColor ? cells.filter((cell) => cell?.toLowerCase() === activeColor.toLowerCase()).length : 0;
  return <aside className="making-panel panel-card">
    <div className="panel-tabs"><button className={tab === 'color' ? 'is-active' : ''} onClick={() => setTab('color')}>颜色</button><button className={tab === 'area' ? 'is-active' : ''} onClick={() => setTab('area')}>区域</button><button className={tab === 'iron' ? 'is-active' : ''} onClick={() => setTab('iron')}>熨烫</button></div>
    {tab === 'color' && <><div className="active-helper"><Focus size={20} /><div><small>当前高亮</small><strong>{activeColor ? work.palette.find((c) => c.hex === activeColor)?.code : '选择一个色号'}</strong><span>{activeColor ? `剩余 ${work.palette.find((c) => c.hex === activeColor)?.remaining ?? 0} 颗` : '点击颜色，只看这一种豆子'}</span></div></div><ColorList colors={work.palette} active={activeColor} onSelect={onColor} showRemaining /><Button fullWidth variant="secondary" icon={<CheckCircle2 size={18} />} onClick={onComplete}>标记当前颜色完成</Button></>}
    {tab === 'area' && <div className="assistant-stack"><div className="coordinate-card"><Crosshair /><span><small>当前坐标</small><strong>{coordinate}</strong><em>{size}×{size} 图纸 · {activeColor ? work.palette.find((c) => c.hex === activeColor)?.code : '未选择色号'}</em></span></div><div className="metric-row"><div><small>图纸格数</small><strong>{size} × {size}</strong></div><div><small>当前色号</small><strong>{currentCount} 颗</strong></div></div><div className="tip-card"><Focus /><p><strong>{activeColor ? '按当前色号铺设' : '先选择一个色号'}</strong><span>{activeColor ? `图纸中共有 ${currentCount} 颗 ${work.palette.find((c) => c.hex === activeColor)?.code}，完成按钮会只标记这些真实格子。` : `当前图纸共有 ${filled} 颗豆子。`}</span></p></div><Button fullWidth icon={<CheckCircle2 size={18} />} onClick={onComplete}>标记当前颜色完成</Button><Button fullWidth variant="ghost" icon={<RotateCcw size={18} />} onClick={onReset}>重置制作进度</Button></div>}
    {tab === 'iron' && <div className="assistant-stack"><div className="risk-card"><AlertTriangle /><p><strong>边缘结构较细</strong><span>翻面时注意散开，建议先固定外围轮廓。</span></p></div><div className="risk-card"><Flame /><p><strong>分区熨烫建议</strong><span>先固定边缘，再处理中心大色块；均匀施压并等待冷却。</span></p></div><p className="fine-print">此功能提供一般性建议，不代替具体材料说明。</p></div>}
  </aside>;
}
