import { AlertTriangle, LoaderCircle, Sparkles } from 'lucide-react';
import type { ReactNode } from 'react';

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <div className="state-card"><span className="state-icon"><Sparkles /></span><h3>{title}</h3><p>{description}</p>{action}</div>;
}
export function LoadingState({ label }: { label: string }) {
  return <div className="state-card"><span className="state-icon"><LoaderCircle className="spin" /></span><h3>{label}</h3><p>请稍候，我们正在整理适合制作的细节。</p></div>;
}
export function ErrorState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <div className="state-card state-error"><span className="state-icon"><AlertTriangle /></span><h3>{title}</h3><p>{description}</p>{action}</div>;
}
