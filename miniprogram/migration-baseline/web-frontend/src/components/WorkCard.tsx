import { MoreHorizontal, Pencil, Play } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { Work } from '../types';
import { BeadGrid } from './BeadGrid';
import { Button } from './Button';
import { IconButton } from './IconButton';

export function WorkCard({ work, compact = false, onMore }: { work: Work; compact?: boolean; onMore?: (work: Work) => void }) {
  const navigate = useNavigate();
  return <article className={`work-card ${compact ? 'compact' : ''}`}>
      <div className="work-preview" role="button" tabIndex={0} onClick={() => navigate(`/editor/${work.id}`)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') navigate(`/editor/${work.id}`); }} aria-label={`打开 ${work.name}`}>{work.grid.length && work.gridSize ? <BeadGrid size={work.gridSize} cells={work.grid} colors={work.palette} /> : work.previewDataUrl ? <img src={work.previewDataUrl} alt="" /> : <BeadGrid motif={work.motif} size={18} />}</div>
    <div className="work-card-body">
      <div className="work-card-title"><div><span className={`status-pill ${work.status === '已完成' ? 'done' : ''}`}>{work.status}</span><h3>{work.name}</h3></div>{onMore && <IconButton aria-label="更多操作" onClick={() => onMore(work)}><MoreHorizontal size={19} /></IconButton>}</div>
      <p>{work.size} · {work.brand} · {work.colors} 色 · {work.beads} 颗</p>
      {!compact && <div className="work-actions"><Button variant="secondary" icon={<Pencil size={16} />} onClick={() => navigate(`/editor/${work.id}`)}>继续编辑</Button><Button variant="ghost" icon={<Play size={16} />} onClick={() => navigate(`/make/${work.id}`)}>开始制作</Button></div>}
    </div>
  </article>;
}
