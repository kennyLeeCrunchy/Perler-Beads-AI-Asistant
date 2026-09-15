import { ChevronDown, RefreshCw, Sparkles, WandSparkles } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { cleanReference, generateAiImage, resolveApiMediaUrl, type AiImageResult, type CleanReferenceResult } from '../api';
import { Button } from '../components/Button';
import { EmptyState, ErrorState, LoadingState } from '../components/States';
import { ResponsivePageContainer } from '../components/ResponsivePageContainer';
import { UploadArea } from '../components/UploadArea';

export function AIGeneratePage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<'text' | 'upload'>('text');
  const [prompt, setPrompt] = useState('');
  const [referenceFile, setReferenceFile] = useState<File>();
  const [referenceTreatment, setReferenceTreatment] = useState<'subject' | 'whole'>('subject');
  const [subjectSituation, setSubjectSituation] = useState<'unknown' | 'single' | 'multiple' | 'none'>('unknown');
  const [targetSubject, setTargetSubject] = useState('');
  const [wholeImageStyle, setWholeImageStyle] = useState<'pixel' | 'cartoon'>('pixel');
  const [brand, setBrand] = useState<'Artkal' | 'Mard'>('Artkal');
  const [size, setSize] = useState('52×52');
  const [transparent, setTransparent] = useState(true);
  const [count, setCount] = useState(2);
  const [status, setStatus] = useState<'empty' | 'loading' | 'done' | 'error'>('empty');
  const [selected, setSelected] = useState(0);
  const [candidates, setCandidates] = useState<AiImageResult[]>([]);
  const [cleanResult, setCleanResult] = useState<CleanReferenceResult>();
  const [error, setError] = useState('');
  const examplePrompt = '一只戴黄色围巾的可爱柴犬，正面，简洁背景';

  const generate = async (promptOverride?: string) => {
    if (mode === 'upload') {
      if (!referenceFile) {
        setError('请先选择一张参考图片。');
        setStatus('error');
        return;
      }
      if (referenceTreatment === 'subject') {
        if (subjectSituation === 'unknown') {
          setError('请先确认图片中主体的情况。当前 APP 尚未接入自动主体识别，暂时需要你手动确认。');
          setStatus('error');
          return;
        }
        if (subjectSituation === 'none') {
          setError('这张图片没有清晰主体，不能使用“主体卡通化”。请改用“整图风格化”，或重新上传包含人物、宠物或明确物体的图片。');
          setStatus('error');
          return;
        }
        if (subjectSituation === 'multiple' && !targetSubject.trim()) {
          setError('图片中有多个主体，请描述要处理的目标，例如“画面左侧穿白衣的人”或“中间的橘猫”。');
          setStatus('error');
          return;
        }
      }
      setStatus('loading');
      setError('');
      try {
        const result = await cleanReference({
          image: referenceFile,
          mode: referenceTreatment === 'subject' ? 'subject' : 'scene',
          subjectTarget: targetSubject,
          prompt: wholeImageStyle === 'pixel' ? '适合拼豆的像素化信息归纳' : '适合拼豆的平滑卡通清稿',
        });
        setCleanResult(result);
        setStatus('done');
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : '参考图清稿失败，请稍后重试。');
        setStatus('error');
      }
      return;
    }
    const effectivePrompt = promptOverride?.trim() || prompt.trim();
    if (!effectivePrompt) {
      setError('请输入图案描述。');
      setStatus('error');
      return;
    }
    setStatus('loading');
    setError('');
    try {
      const results = await Promise.all(
        Array.from({ length: count }, () => generateAiImage(effectivePrompt, transparent)),
      );
      setCandidates(results);
      setSelected(0);
      setStatus('done');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'AI 生图失败，请稍后重试。');
      setStatus('error');
    }
  };

  const convertReferenceDirectly = () => {
    if (!referenceFile) {
      setError('请先选择一张参考图片。');
      setStatus('error');
      return;
    }
    navigate('/convert', { state: { source: 'upload', image: referenceFile, size, transparent, brand } });
  };

  const useCleanReference = () => {
    if (!cleanResult) return;
    navigate('/convert', {
      state: {
        source: 'clean-reference',
        cleanReferenceId: cleanResult.clean_reference_id,
        imageUrl: cleanResult.image_url,
        size,
        transparent: referenceTreatment === 'subject',
        brand,
      },
    });
  };

  const switchMode = (nextMode: 'text' | 'upload') => {
    setMode(nextMode);
    setStatus('empty');
    setError('');
    setCleanResult(undefined);
  };

  const useCandidate = () => {
    const candidate = candidates[selected];
    if (!candidate) return;
    navigate('/convert', {
      state: {
        source: 'ai',
        sourcePath: candidate.source_path,
        imageUrl: candidate.image_url,
        size,
        transparent,
        brand,
      },
    });
  };

  return <ResponsivePageContainer className="page-section">
    <header className="page-heading"><span className="eyebrow">拼豆友好生成</span><h1>AI 创意生图</h1><p>生成主体清晰、颜色分区明确、适合转换为拼豆图纸的图案。</p></header>
    <div className="creator-layout">
      <section className="settings-panel panel-card">
        <div className="panel-tabs large"><button className={mode === 'text' ? 'is-active' : ''} onClick={() => switchMode('text')}>文字生成</button><button className={mode === 'upload' ? 'is-active' : ''} onClick={() => switchMode('upload')}>上传参考图</button></div>
        {mode === 'text'
          ? <label className="field-stack"><span>描述你的创意</span><textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="建议描述主体、视角、配饰和背景复杂度。" /><small>输入内容后灰度提示会自动消失。</small></label>
          : <div className="upload-flow">
            <UploadArea compact onUploaded={(file) => { setReferenceFile(file); setStatus('empty'); setError(''); }} onRemoved={() => { setReferenceFile(undefined); setStatus('empty'); setError(''); }} />
            <div className="field-stack">
              <span>希望怎样处理参考图？</span>
              <div className="reference-mode-cards">
                <button type="button" className={`reference-mode-card ${referenceTreatment === 'subject' ? 'is-active' : ''}`} onClick={() => { setReferenceTreatment('subject'); setStatus('empty'); setError(''); }}>
                  <strong>主体卡通化</strong>
                  <small>只把照片中已有的人物、宠物或明确物体转成卡通形象，不会凭空创造新主体。</small>
                </button>
                <button type="button" className={`reference-mode-card ${referenceTreatment === 'whole' ? 'is-active' : ''}`} onClick={() => { setReferenceTreatment('whole'); setStatus('empty'); setError(''); }}>
                  <strong>整图风格化</strong>
                  <small>保留完整画面和构图，适合风景、建筑以及不需要单独提取主体的图片。</small>
                </button>
              </div>
            </div>
            {referenceTreatment === 'subject'
              ? <div className="reference-options">
                <label className="field-stack">
                  <span>图片中的主体情况</span>
                  <select value={subjectSituation} onChange={(event) => { setSubjectSituation(event.target.value as typeof subjectSituation); setStatus('empty'); setError(''); }}>
                    <option value="unknown">请选择</option>
                    <option value="single">有一个清晰主体</option>
                    <option value="multiple">有多个主体</option>
                    <option value="none">没有清晰主体 / 纯风景</option>
                  </select>
                  <small>正式主体识别尚未接入，目前请根据图片手动确认。</small>
                </label>
                {subjectSituation === 'multiple' && <label className="field-stack">
                  <span>选择要处理的主体</span>
                  <input value={targetSubject} onChange={(event) => setTargetSubject(event.target.value)} placeholder="例如：画面左侧穿白衣的人" />
                  <small>请用位置、衣着或外观描述一个明确目标。</small>
                </label>}
                {subjectSituation === 'none' && <div className="validation-note is-blocked"><strong>当前模式不可用</strong><span>纯风景或无清晰主体的图片不能进行主体卡通化，请切换为“整图风格化”或重新上传。</span></div>}
              </div>
              : <label className="field-stack">
                <span>整图风格</span>
                <div className="segmented">
                  <button type="button" className={wholeImageStyle === 'pixel' ? 'is-active' : ''} onClick={() => setWholeImageStyle('pixel')}>像素风</button>
                  <button type="button" className={wholeImageStyle === 'cartoon' ? 'is-active' : ''} onClick={() => setWholeImageStyle('cartoon')}>卡通风</button>
                </div>
                <small>风格化完成后再进入色卡量化和转图纸流程。</small>
              </label>}
            <div className="info-note flow-explainer"><strong>一次清稿，三档图纸共用</strong><span>后端会先调用一次图生图清稿，再由确定性算法生成 52×52、78×78、104×104 三档图纸，不重复消耗 AI 次数。</span></div>
          </div>}
        <div className={`form-grid ${mode === 'upload' ? 'single-column' : ''}`}><label className="field-stack"><span>品牌色卡</span><select value={brand} onChange={(event) => setBrand(event.target.value as 'Artkal' | 'Mard')}><option value="Artkal">Artkal M 系列</option><option value="Mard">Mard 221 色</option></select><small>转换阶段会匹配所选品牌的真实色号。</small></label></div>
        <div className="field-stack"><span>拼豆板尺寸</span><div className="choice-cards">{['52×52', '78×78', '104×104'].map((item) => <button key={item} className={size === item ? 'is-active' : ''} onClick={() => setSize(item)}><strong>{item}</strong><small>{item === '52×52' ? '轻量挂饰' : item === '78×78' ? '适中细节' : '丰富细节'}</small></button>)}</div><small>尺寸越大，可以保留越多细节，但制作成本也越高。</small></div>
        <div className="switch-card"><div><strong>透明底 / 不规则图形</strong><span>生成干净单主体，背景不参与填豆和数量统计。</span></div><button className={`switch ${transparent ? 'is-on' : ''}`} onClick={() => setTransparent(!transparent)} aria-label="切换透明底"><i /></button></div>
        {transparent && <div className="info-note">开启后，系统会自动去除背景，只保留清晰主体；如果背景过于复杂，会提示你重新生成，避免背景被误算成拼豆。</div>}
        {mode === 'text' && <div className="field-stack"><span>生成数量</span><div className="segmented">{[1, 2, 4].map((item) => <button key={item} className={count === item ? 'is-active' : ''} onClick={() => setCount(item)}>{item} 张</button>)}</div></div>}
        <Button fullWidth icon={<WandSparkles size={18} />} onClick={() => void generate()} disabled={status === 'loading'}>{mode === 'upload' ? 'AI 清稿并继续转图' : status === 'loading' ? '正在调用 AI 服务…' : '生成候选图'}</Button>
        {mode === 'upload' && <button type="button" className="direct-convert-link" onClick={convertReferenceDirectly}>跳过 AI 风格化，直接转为拼豆图纸</button>}
      </section>
      <section className="results-panel panel-card">
        <div className="results-head"><div><span className="eyebrow">{mode === 'upload' ? '参考图处理' : '候选结果'}</span><h2>{mode === 'upload' ? '确认处理方式后再生成' : '选择最接近灵感的一张'}</h2></div>{status === 'done' && <Button variant="ghost" icon={<RefreshCw size={16} />} onClick={() => void generate()}>重新生成</Button>}</div>
        {status === 'empty' && (mode === 'upload'
          ? <EmptyState title="上传图片并选择处理方式" description="主体模式会提取已有的人物、宠物或物体；整图模式保留完整场景。清稿完成后可继续选择三档图纸。" action={<Button variant="secondary" onClick={() => void generate()}>开始 AI 清稿</Button>} />
          : <EmptyState title="生成你的第一组拼豆图案" description="填写描述并选择拼豆友好参数，真实 AI 候选图会出现在这里。" action={<Button variant="secondary" onClick={() => { setPrompt(examplePrompt); void generate(examplePrompt); }}>使用示例生成</Button>} />)}
        {status === 'loading' && <><LoadingState label="AI 正在生成并处理图片" /><div className="generation-steps"><span className="done">理解描述</span><span className="active">调用通义万相</span><span>透明底质量校验</span></div></>}
        {status === 'error' && <ErrorState title="生成没有完成" description={error} action={<Button variant="secondary" onClick={() => void generate()}>重新尝试</Button>} />}
        {status === 'done' && (mode === 'upload' && cleanResult
          ? <><div className="clean-reference-result"><div className="generated-art"><img src={resolveApiMediaUrl(cleanResult.image_url)} alt="AI 清稿结果" /></div><div><span className="success-badge">AI 清稿完成</span><h3>准备生成三档图纸</h3><p>算法版本 {cleanResult.algorithm_version} · AI 调用 {cleanResult.ai_passes} 次</p><p>识别为 {cleanResult.source_type === 'subject' ? '独立主体' : '完整场景'}，下一步将匹配真实 {brand} 色卡。</p></div></div><div className="result-action"><div><Sparkles /><span><small>清稿结果已固定</small><strong>52 / 78 / 104 三档共用同一份清稿</strong></span></div><Button onClick={useCleanReference}>选择尺寸并转为图纸</Button></div></>
          : <><div className="result-grid">{candidates.map((candidate, index) => <button key={candidate.source_path} className={`result-card ${selected === index ? 'is-selected' : ''}`} onClick={() => setSelected(index)}><span className="result-check">{selected === index ? '✓' : ''}</span><div className="generated-art"><img src={resolveApiMediaUrl(candidate.image_url)} alt={`AI 候选图 ${index + 1}`} /></div><footer><span>候选图 {index + 1}</span><small>{size}</small></footer></button>)}</div><div className="result-action"><div><Sparkles /><span><small>已选择候选图 {selected + 1}</small><strong>接下来匹配真实 {brand} 色卡</strong></span></div><Button onClick={useCandidate}>使用这张图并转为拼豆图纸</Button></div></>)}
      </section>
    </div>
    <button className="mobile-sticky-action" onClick={() => void generate()} disabled={status === 'loading'}><Sparkles size={18} />{mode === 'upload' ? '检查风格化设置' : '生成候选图'} <ChevronDown size={16} /></button>
  </ResponsivePageContainer>;
}
