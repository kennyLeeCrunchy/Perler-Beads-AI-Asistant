import { ArrowLeft, CheckCircle2, Crosshair, Download, Eye, Grid3X3, Palette, Settings2 } from 'lucide-react';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { BeadGrid, buildGrid } from '../components/BeadGrid';
import { Button } from '../components/Button';
import { CoordinateBoard } from '../components/CoordinateBoard';
import { Drawer } from '../components/Drawer';
import { ExportPanel } from '../components/ExportPanel';
import { IconButton } from '../components/IconButton';
import { MakingAssistantPanel } from '../components/MakingAssistantPanel';
import { PatternSummary } from '../components/PatternSummary';
import { showToast } from '../components/Toast';
import { seedWorks } from '../demo/seedData';
import type { BeadColor } from '../types';
import { findWork, upsertWork } from '../utils/storage';

export function MakePage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const foundWork = findWork(id);
  const work = foundWork ?? seedWorks[0];
  const gridSize = work.gridSize ?? 24;
  const [tab, setTab] = useState<'make' | 'export'>('make');
  const [activeColor, setActiveColor] = useState<string>();
  const [coordinate, setCoordinate] = useState('X — / Y —');
  const [completed, setCompleted] = useState<Set<number>>(() => {
    try {
      const raw = localStorage.getItem(`perler-progress-${work.id}`);
      return new Set<number>(raw ? JSON.parse(raw) as number[] : []);
    } catch {
      return new Set<number>();
    }
  });
  const [drawer, setDrawer] = useState(false);
  const [grid, setGrid] = useState(true);
  const [showCodes, setShowCodes] = useState(true);
  const [showOutline, setShowOutline] = useState(false);
  const gridCells = work.grid.length === gridSize * gridSize ? work.grid : buildGrid(gridSize, work.motif);
  const filledCount = gridCells.filter(Boolean).length;
  const progressPercent = filledCount ? Math.min(100, Math.round((completed.size / filledCount) * 100)) : work.progress;
  const persistProgress = (next: Set<number>) => {
    const progress = filledCount ? Math.round((next.size / filledCount) * 100) : 0;
    localStorage.setItem(`perler-progress-${work.id}`, JSON.stringify(Array.from(next)));
    upsertWork({ ...work, progress, status: progress >= 100 ? '已完成' : '草稿', updatedAt: new Date().toISOString() });
  };
  const complete = () => {
    if (!activeColor) {
      showToast('请先选择一个色号，再标记当前颜色');
      return;
    }
    const next = new Set(completed);
    gridCells.forEach((cell, index) => { if (cell?.toLowerCase() === activeColor.toLowerCase()) next.add(index); });
    setCompleted(next);
    persistProgress(next);
    showToast(`已标记 ${next.size - completed.size} 颗 ${work.palette.find((color) => color.hex === activeColor)?.code ?? ''}`);
  };
  const resetProgress = () => {
    setCompleted(new Set());
    persistProgress(new Set());
    showToast('制作进度已重置');
  };
  const pickColor = (color: BeadColor) => { setActiveColor((prev) => prev === color.hex ? undefined : color.hex); };
  const toggleCell = (index: number) => setCompleted((prev) => {
    if (!gridCells[index]) return prev;
    const next = new Set(prev);
    next.has(index) ? next.delete(index) : next.add(index);
    persistProgress(next);
    return next;
  });
  if (!foundWork) return <main className="page-section"><div className="state-card state-error"><h1>找不到这件作品</h1><p>作品可能已被删除，或链接已经失效。</p><Button onClick={() => navigate('/works')}>返回我的作品</Button></div></main>;
  return <main className="make-page">
    <header className="make-header"><IconButton onClick={() => navigate(`/editor/${work.id}`)} aria-label="返回编辑器"><ArrowLeft /></IconButton><div className="make-title"><span className="mini-preview">{work.previewDataUrl ? <img src={work.previewDataUrl} alt="" /> : <BeadGrid motif={work.motif} size={10} />}</span><div><span className="eyebrow">制作中的作品</span><h1>{work.name}</h1></div></div><PatternSummary work={work} compact /><IconButton className="make-settings" onClick={() => setDrawer(true)}><Settings2 /></IconButton></header>
    <div className="make-tabs"><button className={tab === 'make' ? 'is-active' : ''} onClick={() => setTab('make')}>制作辅助</button><button className={tab === 'export' ? 'is-active' : ''} onClick={() => setTab('export')}>导出图纸</button></div>
    {tab === 'make' ? <div className="making-layout"><section className="making-canvas panel-card"><div className="canvas-controls"><div><Button variant="ghost" icon={<Grid3X3 size={17} />} onClick={() => setGrid(!grid)}>{grid ? '隐藏网格' : '显示网格'}</Button><Button variant="ghost" icon={<Crosshair size={17} />} onClick={() => setShowCodes(!showCodes)}>{showCodes ? '隐藏色号' : '显示色号'}</Button><Button variant="ghost" icon={<Eye size={17} />} onClick={() => setShowOutline(!showOutline)}>{showOutline ? '隐藏轮廓' : '外轮廓'}</Button></div><span className="progress-chip"><i style={{ width: `${progressPercent}%` }} />制作进度 {progressPercent}%</span></div><div className={`making-grid-stage ${grid ? '' : 'no-grid'}`}><CoordinateBoard size={gridSize} assist guideLabel={activeColor ? '连续同色区域' : undefined}><BeadGrid motif={work.motif} size={gridSize} cells={work.grid.length ? work.grid : undefined} colors={work.palette} highlightedColor={activeColor} completed={completed} showNumbers={showCodes} showOutline={showOutline} displayMode="pattern" onCellClick={toggleCell} onCellHover={(x, y) => setCoordinate(`X ${x} / Y ${y}`)} /></CoordinateBoard></div><footer className="making-status"><span><Crosshair size={16} />{coordinate}</span><span>{activeColor ? `当前 ${work.palette.find((color) => color.hex === activeColor)?.code}` : '点击色号开始高亮'}</span><span>已标记 {completed.size} / {filledCount} 格</span></footer></section><MakingAssistantPanel work={work} activeColor={activeColor} onColor={pickColor} coordinate={coordinate} onComplete={complete} onReset={resetProgress} /></div> : <ExportPanel work={work} />}
    {tab === 'make' && <div className="mobile-making-bar"><button onClick={() => setDrawer(true)}><Palette /><span>颜色</span></button><button onClick={() => setDrawer(true)}><Eye /><span>高亮</span></button><button><Crosshair /><span>坐标</span></button><button onClick={complete}><CheckCircle2 /><span>完成</span></button><button onClick={() => setTab('export')}><Download /><span>导出</span></button></div>}
    <Drawer open={drawer} title="制作辅助" onClose={() => setDrawer(false)}><MakingAssistantPanel work={work} activeColor={activeColor} onColor={pickColor} coordinate={coordinate} onComplete={complete} onReset={resetProgress} /></Drawer>
  </main>;
}
