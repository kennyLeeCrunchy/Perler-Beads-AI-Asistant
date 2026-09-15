import { ArrowLeft, Check, ChevronDown, FlipHorizontal2, MoreHorizontal, Redo2, Save, Undo2 } from 'lucide-react';
import { useMemo, useState, type WheelEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { BeadGrid, buildGrid, type GridTool } from '../components/BeadGrid';
import { Button } from '../components/Button';
import { ColorList } from '../components/ColorList';
import { CoordinateBoard } from '../components/CoordinateBoard';
import { Drawer } from '../components/Drawer';
import { EditorToolbar, MobileEditorToolbar } from '../components/EditorToolbar';
import { IconButton } from '../components/IconButton';
import { Modal } from '../components/Modal';
import { PatternSummary } from '../components/PatternSummary';
import { showToast } from '../components/Toast';
import { palette, seedWorks } from '../demo/seedData';
import type { BeadColor } from '../types';
import { findWork, upsertWork } from '../utils/storage';

type PanelTab = 'color' | 'selection' | 'info';
const MIN_CANVAS_ZOOM = 0.75;
const MAX_CANVAS_ZOOM = 4;
const CODE_ZOOM_THRESHOLD = 1.75;

export function EditorPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const foundWork = useMemo(() => findWork(id === 'demo' ? 'girl' : id), [id]);
  const baseWork = foundWork ?? seedWorks[0];
  const gridSize = baseWork.gridSize ?? 24;
  const [name, setName] = useState(baseWork.name);
  const [tool, setTool] = useState<GridTool>('select');
  const [selected, setSelected] = useState(new Set<number>());
  const [activeColor, setActiveColor] = useState<BeadColor>(baseWork.palette[1] ?? baseWork.palette[0] ?? palette[1]);
  const [highlighted, setHighlighted] = useState<string>();
  const [overrides, setOverrides] = useState(new Map<number, string | null>());
  const [history, setHistory] = useState<Array<Map<number, string | null>>>([]);
  const [future, setFuture] = useState<Array<Map<number, string | null>>>([]);
  const [dirty, setDirty] = useState(false);
  const [mirror, setMirror] = useState(false);
  const [tab, setTab] = useState<PanelTab>('color');
  const [replaceOpen, setReplaceOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [coordinate, setCoordinate] = useState('X — / Y —');
  const baseGrid = useMemo(
    () => baseWork.grid.length === gridSize * gridSize ? baseWork.grid : buildGrid(gridSize, baseWork.motif),
    [baseWork.grid, baseWork.motif, gridSize],
  );
  const replacementColor = baseWork.palette.find((item) => item.hex !== (highlighted ?? activeColor.hex)) ?? activeColor;
  const showCodes = zoom >= CODE_ZOOM_THRESHOLD;
  const handleCanvasWheel = (event: WheelEvent<HTMLElement>) => {
    if (!event.ctrlKey) return;
    event.preventDefault();
    setZoom((current) => Math.min(MAX_CANVAS_ZOOM, Math.max(MIN_CANVAS_ZOOM, current * (event.deltaY < 0 ? 1.1 : 0.9))));
  };
  const pushChange = (next: Map<number, string | null>) => { setHistory((prev) => [...prev.slice(-19), new Map(overrides)]); setOverrides(next); setFuture([]); setDirty(true); };
  const undo = () => { const previous = history.at(-1); if (!previous) return; setFuture((prev) => [new Map(overrides), ...prev]); setOverrides(new Map(previous)); setHistory((prev) => prev.slice(0, -1)); setDirty(true); };
  const redo = () => { const next = future[0]; if (!next) return; setHistory((prev) => [...prev, new Map(overrides)]); setOverrides(new Map(next)); setFuture((prev) => prev.slice(1)); setDirty(true); };
  const onCell = (index: number, color: string | null, event: React.MouseEvent<HTMLButtonElement>) => {
    if (tool === 'paint') { const next = new Map(overrides); next.set(index, activeColor.hex); pushChange(next); return; }
    if (tool === 'erase') { const next = new Map(overrides); next.set(index, null); pushChange(next); return; }
    if (tool === 'picker' && color) { const found = baseWork.palette.find((item) => item.hex.toLowerCase() === color.toLowerCase()); if (found) setActiveColor(found); setTool('paint'); return; }
    if (tool === 'box') { const x = index % gridSize; const y = Math.floor(index / gridSize); const next = new Set<number>(); for (let dy = 0; dy < 3; dy++) for (let dx = 0; dx < 4; dx++) { const nx = x + dx; const ny = y + dy; if (nx < gridSize && ny < gridSize) next.add(ny * gridSize + nx); } setSelected(next); setTab('selection'); return; }
    if (tool === 'select') { setSelected((prev) => { const next = event.ctrlKey ? new Set(prev) : new Set<number>(); if (next.has(index)) next.delete(index); else next.add(index); return next; }); setTab('selection'); }
  };
  const fillSelection = (color: string | null) => { if (!selected.size) return; const next = new Map(overrides); selected.forEach((index) => next.set(index, color)); pushChange(next); };
  const replaceColor = () => { const from = highlighted ?? activeColor.hex; const next = new Map(overrides); baseGrid.forEach((base, index) => { const current = overrides.has(index) ? overrides.get(index) ?? null : base; if (current === from && (!selected.size || selected.has(index))) next.set(index, replacementColor.hex); }); pushChange(next); setReplaceOpen(false); setHighlighted(replacementColor.hex); showToast(selected.size ? '已替换选区内同色豆子' : '已替换全图同色豆子'); };
  const save = () => {
    const grid = baseGrid.map((base, index) => overrides.has(index) ? overrides.get(index) ?? null : base);
    const counts = new Map<string, number>();
    grid.forEach((hex) => { if (hex) counts.set(hex.toLowerCase(), (counts.get(hex.toLowerCase()) ?? 0) + 1); });
    const nextPalette = baseWork.palette
      .map((color) => ({ ...color, count: counts.get(color.hex.toLowerCase()) ?? 0, remaining: counts.get(color.hex.toLowerCase()) ?? 0 }))
      .filter((color) => color.count > 0);
    try {
      upsertWork({
        ...baseWork,
        id: id === 'demo' ? `work-${Date.now()}` : baseWork.id,
        name,
        grid,
        colors: nextPalette.length,
        beads: grid.filter(Boolean).length,
        updatedAt: new Date().toISOString(),
        palette: nextPalette,
        previewDataUrl: undefined,
        mirror,
      });
      setDirty(false);
      showToast('作品和颜色统计已保存到当前浏览器');
    } catch {
      showToast('浏览器存储空间不足，作品未能保存');
    }
  };
  if (!foundWork) return <main className="page-section"><div className="state-card state-error"><h1>找不到这件作品</h1><p>作品可能已被删除，或链接已经失效。</p><Button onClick={() => navigate('/works')}>返回我的作品</Button></div></main>;
  return <main className="editor-page">
    <header className="editor-command-bar"><div className="editor-title"><IconButton onClick={() => navigate('/works')} aria-label="返回作品"><ArrowLeft size={20} /></IconButton><input value={name} onChange={(e) => { setName(e.target.value); setDirty(true); }} /><span className={dirty ? 'dirty' : ''}>{dirty ? '有未保存修改' : '已保存'}</span></div><div className="editor-center-actions"><IconButton onClick={undo} disabled={!history.length}><Undo2 /></IconButton><IconButton onClick={redo} disabled={!future.length}><Redo2 /></IconButton><button className={`text-tool ${mirror ? 'is-active' : ''}`} onClick={() => setMirror(!mirror)}><FlipHorizontal2 />{mirror ? '镜像' : '正面'}</button><span className="zoom-label">{Math.round(zoom * 100)}%</span></div><div className="editor-main-actions"><Button variant="secondary" icon={<Save size={17} />} onClick={save}>保存</Button><Button onClick={() => navigate(`/make/${baseWork.id}`)}>制作辅助</Button><IconButton className="editor-more" onClick={() => setDrawerOpen(true)}><MoreHorizontal /></IconButton></div></header>
    <div className="editor-workspace"><EditorToolbar active={tool} onChange={setTool} onUndo={undo} onRedo={redo} /><section className="canvas-area" onWheel={handleCanvasWheel}><CoordinateBoard size={gridSize} mirror={mirror} zoom={zoom}><BeadGrid motif={baseWork.motif} size={gridSize} cells={baseGrid} colors={baseWork.palette} selected={selected} highlightedColor={highlighted} mirror={mirror} showNumbers={showCodes} displayMode="pattern" overrides={overrides} onCellClick={onCell} onCellHover={(x, y) => setCoordinate(`X ${x} / Y ${y}`)} /></CoordinateBoard><div className="canvas-hint">Ctrl + 滚轮缩放 · {showCodes ? '当前已显示色号' : `放大到 ${Math.round(CODE_ZOOM_THRESHOLD * 100)}% 后显示色号`}</div></section><aside className="editor-properties panel-card"><div className="panel-tabs"><button className={tab === 'color' ? 'is-active' : ''} onClick={() => setTab('color')}>颜色</button><button className={tab === 'selection' ? 'is-active' : ''} onClick={() => setTab('selection')}>选区</button><button className={tab === 'info' ? 'is-active' : ''} onClick={() => setTab('info')}>信息</button></div>{tab === 'color' && <><div className="brand-row"><span>当前色卡</span><strong>{baseWork.brand}</strong></div><ColorList colors={baseWork.palette} active={activeColor.hex} onSelect={(color) => { setActiveColor(color); setHighlighted(color.hex); }} /><div className="property-actions"><Button variant="secondary" onClick={() => setReplaceOpen(true)}>替换全图同色</Button><Button variant="ghost" onClick={() => setHighlighted(undefined)}>取消高亮</Button></div></>}{tab === 'selection' && <div className="selection-panel"><div className="selection-hero"><strong>{selected.size}</strong><span>个格子已选中</span></div><div className="metric-row"><div><small>选区宽高</small><strong>{selected.size ? '4 × 3' : '—'}</strong></div><div><small>当前颜色</small><strong>{activeColor.code}</strong></div></div><Button fullWidth onClick={() => fillSelection(activeColor.hex)}>填充当前颜色</Button><Button fullWidth variant="secondary" onClick={() => fillSelection(null)}>擦除选区</Button><Button fullWidth variant="ghost" onClick={() => setSelected(new Set())}>清除选择</Button></div>}{tab === 'info' && <PatternSummary work={baseWork} />}</aside></div>
    <footer className="editor-status"><span>{coordinate}</span><span>当前色号 {activeColor.code}</span><span>缩放 {Math.round(zoom * 100)}%</span><span>已选 {selected.size} 格</span><span>{baseWork.brand} 色卡</span></footer>
    <MobileEditorToolbar active={tool} onChange={setTool} onUndo={undo} /><button className="mobile-editor-drawer-button" onClick={() => setDrawerOpen(true)}><span style={{ background: activeColor.hex }} />颜色 / 选区 / 信息<ChevronDown size={17} /></button>
    <Drawer open={drawerOpen} title="编辑属性" onClose={() => setDrawerOpen(false)}><div className="panel-tabs"><button className={tab === 'color' ? 'is-active' : ''} onClick={() => setTab('color')}>颜色</button><button className={tab === 'selection' ? 'is-active' : ''} onClick={() => setTab('selection')}>选区</button><button className={tab === 'info' ? 'is-active' : ''} onClick={() => setTab('info')}>信息</button></div>{tab === 'color' && <ColorList colors={baseWork.palette} active={activeColor.hex} onSelect={(color) => { setActiveColor(color); setHighlighted(color.hex); }} />}{tab === 'selection' && <div className="selection-panel"><strong>{selected.size} 格已选中</strong><Button fullWidth onClick={() => fillSelection(activeColor.hex)}>填充当前颜色</Button></div>}{tab === 'info' && <PatternSummary work={baseWork} />}</Drawer>
    <Modal open={replaceOpen} title="替换同色豆子" onClose={() => setReplaceOpen(false)} actions={<><Button variant="ghost" onClick={() => setReplaceOpen(false)}>取消</Button><Button onClick={replaceColor}>确认替换</Button></>}><div className="replace-preview"><span style={{ background: highlighted ?? activeColor.hex }} /><ArrowLeft /><span style={{ background: replacementColor.hex }} /></div><p>将把{selected.size ? `选区内的` : '全图'}同色豆子替换为 {replacementColor.code}，操作可撤销。</p></Modal>
  </main>;
}
