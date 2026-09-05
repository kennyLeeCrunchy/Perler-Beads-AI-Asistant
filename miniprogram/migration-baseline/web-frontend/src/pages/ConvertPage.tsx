import { ArrowRight, Check, ChevronDown, Crop, ImageUp, RotateCcw, RotateCw, SlidersHorizontal } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { generatePattern, resolveApiMediaUrl, type PatternResult } from '../api';
import { BeadGrid } from '../components/BeadGrid';
import { Button } from '../components/Button';
import { ErrorState } from '../components/States';
import { PatternSummary } from '../components/PatternSummary';
import { ResponsivePageContainer } from '../components/ResponsivePageContainer';
import { UploadArea } from '../components/UploadArea';
import type { BeadColor, Work } from '../types';
import { upsertWork } from '../utils/storage';

type ConvertState = {
  source?: 'ai' | 'upload';
  sourcePath?: string;
  imageUrl?: string;
  image?: File;
  size?: string;
  transparent?: boolean;
  brand?: 'Artkal' | 'Mard';
};

const allowedSizes = ['52×52', '78×78', '104×104'] as const;

export function ConvertPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const routeState = (location.state as ConvertState | null) ?? {};
  const fromAI = routeState.source === 'ai';
  const [imageFile, setImageFile] = useState<File | undefined>(routeState.image);
  const [brand, setBrand] = useState<'Artkal' | 'Mard'>(routeState.brand ?? 'Artkal');
  const [localPreview, setLocalPreview] = useState('');
  const [size, setSize] = useState<typeof allowedSizes[number]>(
    allowedSizes.includes(routeState.size as typeof allowedSizes[number]) ? routeState.size as typeof allowedSizes[number] : '52×52',
  );
  const [board, setBoard] = useState('单板');
  const [removeBg, setRemoveBg] = useState(routeState.transparent ?? true);
  const [maxColors, setMaxColors] = useState(24);
  const [similarity, setSimilarity] = useState(18);
  const [status, setStatus] = useState<'ready' | 'loading' | 'done' | 'error'>('ready');
  const [error, setError] = useState('');
  const [pattern, setPattern] = useState<PatternResult>();
  const [work, setWork] = useState<Work>();
  const uploaded = Boolean(imageFile || routeState.sourcePath);

  useEffect(() => () => {
    if (localPreview) URL.revokeObjectURL(localPreview);
  }, [localPreview]);

  const previewUrl = localPreview || (routeState.imageUrl ? resolveApiMediaUrl(routeState.imageUrl) : '');
  const grid = useMemo(() => {
    if (!pattern) return [];
    const hexByCode = new Map(pattern.counts.map((item) => [item.code, item.hex]));
    return pattern.cells.flat().map((code) => code ? hexByCode.get(code) ?? null : null);
  }, [pattern]);
  const palette = useMemo<BeadColor[]>(() => pattern?.counts.map((item) => ({
    brand,
    code: item.code,
    name: item.name,
    hex: item.hex,
    count: item.count,
    remaining: item.count,
  })) ?? [], [brand, pattern]);

  const chooseImage = (file: File) => {
    if (localPreview) URL.revokeObjectURL(localPreview);
    setImageFile(file);
    setLocalPreview(URL.createObjectURL(file));
    setPattern(undefined);
    setWork(undefined);
    setStatus('ready');
  };

  const clearImage = () => {
    if (localPreview) URL.revokeObjectURL(localPreview);
    setLocalPreview('');
    setImageFile(undefined);
    setPattern(undefined);
    setWork(undefined);
    setStatus('ready');
  };

  const generate = async () => {
    if (!uploaded) return;
    setStatus('loading');
    setError('');
    try {
      const gridSize = Number.parseInt(size, 10);
      const result = await generatePattern({
        image: imageFile,
        sourcePath: imageFile ? undefined : routeState.sourcePath,
        brand,
        width: gridSize,
        height: gridSize,
        maxColors,
        similarityThreshold: similarity,
        useTransparentMask: removeBg,
      });
      const hexByCode = new Map(result.counts.map((item) => [item.code, item.hex]));
      const realGrid = result.cells.flat().map((code) => code ? hexByCode.get(code) ?? null : null);
      const realPalette: BeadColor[] = result.counts.map((item) => ({
        brand,
        code: item.code,
        name: item.name,
        hex: item.hex,
        count: item.count,
        remaining: item.count,
      }));
      const now = new Date().toISOString();
      const nextWork: Work = {
        id: `pattern-${result.pattern_id}`,
        name: fromAI ? 'AI 生成拼豆图纸' : (imageFile?.name.replace(/\.[^.]+$/, '') || '新拼豆图纸'),
        size,
        gridSize,
        board,
        brand,
        colors: result.counts.length,
        beads: result.counts.reduce((total, item) => total + item.count, 0),
        status: '草稿',
        createdAt: now,
        updatedAt: now,
        progress: 0,
        palette: realPalette,
        grid: realGrid,
        patternId: result.pattern_id,
        previewDataUrl: result.preview_data_url,
        motif: fromAI ? 'dog' : 'whale',
      };
      upsertWork(nextWork);
      setPattern(result);
      setWork(nextWork);
      setStatus('done');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '图纸转换失败，请检查后端服务。');
      setStatus('error');
    }
  };

  return <ResponsivePageContainer className="page-section">
    <header className="page-heading"><span className="eyebrow">三步完成转换</span><h1>图片转拼豆图纸</h1><div className="progress-steps"><span className="is-active"><i>1</i>选择图片</span><ArrowRight /><span className={uploaded ? 'is-active' : ''}><i>2</i>设置图纸</span><ArrowRight /><span className={status === 'done' ? 'is-active' : ''}><i>3</i>生成预览</span></div></header>
    <div className="convert-layout">
      <section className="image-panel panel-card">
        <div className="panel-title"><div><span>01</span><h2>选择并调整图片</h2></div><small>JPG / PNG · 最大 10MB</small></div>
        <div className="info-note flow-explainer"><strong>原图将由真实算法转换</strong><span>后端会完成网格采样、透明背景处理和所选品牌色卡匹配，不再使用前端 Mock 图案。</span></div>
        {!uploaded ? <UploadArea onUploaded={chooseImage} /> : <div className={`crop-preview ${removeBg ? 'checkerboard' : ''}`}>{previewUrl ? <img className="source-preview-image" src={previewUrl} alt="待转换图片" /> : <div className="source-ready"><ImageUp size={42} /><strong>{imageFile?.name || 'AI 图片已就绪'}</strong></div>}<div className="crop-frame"><i /><i /><i /><i /></div></div>}
        {uploaded && <div className="preview-tools"><Button variant="ghost" icon={<Crop size={17} />} disabled>裁剪</Button><Button variant="ghost" icon={<RotateCw size={17} />} disabled>旋转</Button><Button variant="ghost" icon={<RotateCcw size={17} />} disabled>重置</Button><Button variant="secondary" icon={<ImageUp size={17} />} onClick={clearImage}>更换图片</Button></div>}
        <div className="field-stack"><span>风格预处理</span><div className="choice-cards three"><button className="is-active"><strong>保留原图</strong><small>当前真实算法管线</small></button><button disabled><strong>像素风</strong><small>待接图生图服务</small></button><button disabled><strong>卡通风</strong><small>待接图生图服务</small></button></div></div>
      </section>
      <section className="parameters-panel panel-card">
        <div className="panel-title"><div><span>02</span><h2>设置图纸参数</h2></div><SlidersHorizontal size={20} /></div>
        <div className="form-grid"><label className="field-stack"><span>品牌色卡</span><select value={brand} onChange={(event) => setBrand(event.target.value as 'Artkal' | 'Mard')}><option value="Artkal">Artkal M 系列</option><option value="Mard">Mard 221 色</option></select><small>量化、色号和用量统计都会使用所选品牌。</small></label><label className="field-stack"><span>最大颜色数量</span><select value={maxColors} onChange={(event) => setMaxColors(Number(event.target.value))}><option value={12}>12 色</option><option value={24}>24 色</option><option value={36}>36 色</option><option value={0}>根据色卡自动</option></select></label></div>
        <div className="field-stack"><span>拼豆板尺寸</span><div className="segmented">{allowedSizes.map((item) => <button key={item} className={size === item ? 'is-active' : ''} onClick={() => setSize(item)}>{item}</button>)}</div><small>尺寸越大细节越多，同时会增加处理时间和制作成本。</small></div>
        <div className="field-stack"><span>拼板配置</span><div className="board-options">{['单板', '横向两块', '纵向两块', '2×2 拼板'].map((item, index) => <button key={item} className={board === item ? 'is-active' : ''} onClick={() => setBoard(item)}><span className={`board-icon board-${index + 1}`}><i /><i /><i /><i /></span><strong>{item}</strong>{board === item && <Check size={16} />}</button>)}</div></div>
        <div className="switch-list"><div><span><strong>自动移除背景</strong><small>使用后端 mask，透明区域不参与统计</small></span><button className={`switch ${removeBg ? 'is-on' : ''}`} onClick={() => setRemoveBg(!removeBg)}><i /></button></div><div><span><strong>边缘平滑</strong><small>由后端量化管线自动执行</small></span><button className="switch is-on" disabled><i /></button></div></div>
        <label className="field-stack"><span>相似色合并</span><div className="segmented"><button className={similarity === 0 ? 'is-active' : ''} onClick={() => setSimilarity(0)}>关闭</button><button className={similarity === 18 ? 'is-active' : ''} onClick={() => setSimilarity(18)}>标准</button><button className={similarity === 28 ? 'is-active' : ''} onClick={() => setSimilarity(28)}>强</button></div></label>
        <Button fullWidth disabled={!uploaded || status === 'loading'} onClick={generate}>{status === 'loading' ? '后端正在匹配色卡和计算数量…' : '生成真实拼豆图纸'}</Button>
        {status === 'error' && <ErrorState title="转换没有完成" description={error} action={<Button variant="secondary" onClick={generate}>重新尝试</Button>} />}
      </section>
    </div>
    {status === 'done' && pattern && work && <section className="conversion-result panel-card"><div className="result-preview"><span className="success-badge"><Check size={17} />真实图纸生成完成</span><BeadGrid size={pattern.width} cells={grid} colors={palette} /></div><div className="result-summary"><span className="eyebrow">转换结果</span><h2>{work.name}</h2><p>已根据 {brand} 色卡完成颜色匹配；作品数据已保存到当前浏览器，可继续逐格编辑。</p><PatternSummary work={work} /><div className="dominant-colors"><span>主色</span>{palette.slice(0, 8).map((color) => <i key={color.code} style={{ background: color.hex }} title={`${color.code} · ${color.count} 颗`} />)}</div><div className="result-buttons"><Button variant="secondary" onClick={() => setStatus('ready')}>重新调整参数</Button><Button onClick={() => navigate(`/editor/${work.id}`)}>进入图纸编辑器 <ArrowRight size={17} /></Button></div></div></section>}
    <button className="mobile-sticky-action" disabled={!uploaded || status === 'loading'} onClick={generate}>生成拼豆图纸 <ChevronDown size={16} /></button>
  </ResponsivePageContainer>;
}
