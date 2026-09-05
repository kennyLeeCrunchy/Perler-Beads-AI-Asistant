import type { ReactNode } from 'react';
import { X } from 'lucide-react';
import { IconButton } from './IconButton';

export function Drawer({ open, title, children, onClose }: { open: boolean; title: string; children: ReactNode; onClose: () => void }) {
  return (
    <div className={`drawer-layer ${open ? 'is-open' : ''}`} aria-hidden={!open}>
      <div className="drawer-backdrop" onClick={onClose} />
      <section className="drawer">
        <div className="drawer-handle" />
        <header><h2>{title}</h2><IconButton aria-label="关闭" onClick={onClose}><X size={20} /></IconButton></header>
        <div className="drawer-body">{children}</div>
      </section>
    </div>
  );
}
