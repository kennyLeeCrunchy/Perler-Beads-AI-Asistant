import { CheckCircle2, Download, FileImage, FileText } from 'lucide-react';
import { useMemo, useState } from 'react';
import { exportPatternPng } from '../api';
import type { Work } from '../types';
import { BeadGrid, buildGrid } from './BeadGrid';
import { Button } from './Button';
import { showToast } from './Toast';

const options = ['显示色号'];

export function ExportPanel({ work }: { work: Work }) {
  const [selected, setSelected] = useState(new Set(options));
  const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle');
  const gridSize = work.gridSize ?? 24;
  const cells = useMemo(
    () => work.grid.length === gridSize * gridSize ? work.grid : buildGrid(gridSize, work.motif),
    [gridSize, work.grid, work.motif],
  );
  const toggle = (option: string) => setSelected((prev) => {
    const next = new Set(prev);
    next.has(option) ? next.delete(option) : next.add(option);
    return next;
  });

  const run = async () => {
    setStatus('loading');
    try {
      const codeByHex = new Map(work.palette.map((color) => [color.hex.toLowerCase(), color.code]));
      const codeCells = Array.from({ length: gridSize }, (_, row) =>
        cells.slice(row * gridSize, (row + 1) * gridSize).map((hex) => hex ? codeByHex.get(hex.toLowerCase()) ?? null : null),
      );
      const blob = await exportPatternPng({
        patternId: work.patternId,
        width: gridSize,
        height: gridSize,
        cells: codeCells,
        colors: work.palette.map((color) => ({ code: color.code, hex: color.hex, name: color.name })),
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${work.name || 'pindou-pattern'}.png`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      setStatus('done');
      showToast('真实 PNG 图纸已生成并开始下载');
    } catch (reason) {
      setStatus('error');
      showToast(reason instanceof Error ? reason.message : '导出失败，请检查后端服务');
    }
  };

  return <div className="export-layout">
    <section className="export-settings panel-card">
      <div className="section-title"><div><span className="eyebrow">导出设置</span><h2>制作一份清楚的图纸</h2></div></div>
      <fieldset><legend>导出内容</legend><label><input type="radio" name="content" defaultChecked />完整图纸</label><label><input type="radio" name="content" disabled />分区图纸（后续）</label><label><input type="radio" name="content" disabled />镜像图纸（后续）</label></fieldset>
      <fieldset><legend>文件格式</legend><div className="format-options"><button className="is-active"><FileImage />PNG<small>已接入后端真实导出</small></button><button disabled><FileText />PDF<small>后端暂未提供</small></button></div></fieldset>
      <fieldset><legend>页面预览</legend><div className="check-grid">{options.map((option) => <label key={option}><input type="checkbox" checked={selected.has(option)} onChange={() => toggle(option)} />{option}</label>)}</div><small>当前后端 PNG 输出为纯图纸；坐标、分板线和统计版式将在 PDF 导出阶段接入。</small></fieldset>
      <Button fullWidth icon={status === 'done' ? <CheckCircle2 size={18} /> : <Download size={18} />} onClick={run} disabled={status === 'loading'}>{status === 'loading' ? '后端正在生成 PNG…' : status === 'error' ? '重试导出 PNG' : status === 'done' ? '再次下载 PNG' : '生成并下载 PNG 图纸'}</Button>
    </section>
    <section className="export-preview panel-card"><div className="preview-head"><div><span className="eyebrow">导出预览</span><h3>{work.name}</h3></div><span className="paper-size">PNG · 真实图纸</span></div><div className="paper"><BeadGrid motif={work.motif} size={gridSize} cells={cells} colors={work.palette} showNumbers={selected.has('显示色号')} /><footer><span>{work.size}</span><span>{work.brand} · {work.colors} 色</span><span>{work.beads} 颗</span></footer></div></section>
  </div>;
}
