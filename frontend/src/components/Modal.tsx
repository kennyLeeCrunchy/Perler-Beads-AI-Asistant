import type { ReactNode } from 'react';
import { X } from 'lucide-react';
import { IconButton } from './IconButton';

export function Modal({ open, title, children, onClose, actions }: { open: boolean; title: string; children: ReactNode; onClose: () => void; actions?: ReactNode }) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="modal" role="dialog" aria-modal="true" aria-label={title} onMouseDown={(e) => e.stopPropagation()}>
        <header><h2>{title}</h2><IconButton aria-label="关闭" onClick={onClose}><X size={20} /></IconButton></header>
        <div className="modal-body">{children}</div>
        {actions && <footer>{actions}</footer>}
      </section>
    </div>
  );
}
