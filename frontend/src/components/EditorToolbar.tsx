import { Eraser, Hand, MousePointer2, Paintbrush, Pipette, Redo2, Scan, Undo2, ZoomIn } from 'lucide-react';
import type { GridTool } from './BeadGrid';

const tools: Array<{ id: GridTool; label: string; icon: typeof MousePointer2 }> = [
  { id: 'select', label: '选择', icon: MousePointer2 }, { id: 'paint', label: '画笔', icon: Paintbrush },
  { id: 'erase', label: '橡皮擦', icon: Eraser }, { id: 'picker', label: '吸色', icon: Pipette },
  { id: 'box', label: '框选', icon: Scan }, { id: 'pan', label: '移动画布', icon: Hand },
];

export function EditorToolbar({ active, onChange, onUndo, onRedo }: { active: GridTool; onChange: (tool: GridTool) => void; onUndo: () => void; onRedo: () => void }) {
  return <aside className="editor-tools">{tools.map(({ id, label, icon: Icon }) => <button key={id} title={label} className={active === id ? 'is-active' : ''} onClick={() => onChange(id)}><Icon size={20} /><span>{label}</span></button>)}<hr /><button onClick={onUndo}><Undo2 size={20} /><span>撤销</span></button><button onClick={onRedo}><Redo2 size={20} /><span>重做</span></button><button><ZoomIn size={20} /><span>缩放</span></button></aside>;
}

export function MobileEditorToolbar({ active, onChange, onUndo }: { active: GridTool; onChange: (tool: GridTool) => void; onUndo: () => void }) {
  return <div className="mobile-editor-tools"><span className="current-color"><i />当前 M23</span>{tools.slice(0, 5).map(({ id, label, icon: Icon }) => <button key={id} className={active === id ? 'is-active' : ''} onClick={() => onChange(id)}><Icon size={20} /><span>{label}</span></button>)}<button onClick={onUndo}><Undo2 size={20} /><span>撤销</span></button></div>;
}
