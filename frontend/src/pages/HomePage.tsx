import { ArrowRight, Grid3X3, ImageUp, MapPin, Palette, Sparkles, WandSparkles } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BeadGrid } from '../components/BeadGrid';
import { Button } from '../components/Button';
import { Modal } from '../components/Modal';
import { ResponsivePageContainer } from '../components/ResponsivePageContainer';
import { WorkCard } from '../components/WorkCard';
import { seedWorks } from '../demo/seedData';

const capabilities = [
  { icon: WandSparkles, title: 'AI 创作', copy: '输入描述或上传参考图，生成主体清楚、适合拼豆转换的图案。', accent: 'coral', detail: '先从一句创意描述或一张参考图开始，生成适合后续转成拼豆图纸的候选图。', points: ['支持文字生成和参考图生成', '可选择拼豆板尺寸与品牌色卡', '生成后可继续编辑、导出和制作'], cta: '开始 AI 创作', route: '/ai-generate' },
  { icon: Palette, title: '智能转图', copy: '匹配真实品牌色卡，自动统计色号、数量和透明区域。', accent: 'blue', detail: '把已有图片转换成可以实际制作的拼豆图纸，并把颜色、数量和透明区域整理清楚。', points: ['自动提取主体并清理背景', '匹配真实品牌色卡与色号', '生成后可进入编辑器调整细节'], cta: '开始智能转图', route: '/convert' },
  { icon: MapPin, title: '制作辅助', copy: '用高亮、坐标、边界和熨烫提示，减少摆错和漏摆。', accent: 'green', detail: '制作辅助需要先选择一件已有的拼豆作品，再根据图纸逐格完成摆放。', points: ['选择作品后进入制作辅助工作区', '按色号高亮、查看坐标和完成进度', '制作完成后可以导出图纸'], cta: '选择一件作品', route: '/works' },
];

export function HomePage() {
  const navigate = useNavigate();
  const [activeCapability, setActiveCapability] = useState<typeof capabilities[number] | null>(null);
  return <main>
    <ResponsivePageContainer className="hero-section">
      <section className="hero-copy">
        <span className="hero-kicker"><Sparkles size={16} />从灵感到完成，一站式拼豆创作</span>
        <h1>把脑海里的灵感，<br />变成可以亲手完成的<span>拼豆作品</span></h1>
        <p>从 AI 生图、照片转图纸，到改色、坐标定位和制作辅助，一站式完成你的拼豆创作。</p>
        <div className="hero-actions"><Button icon={<Sparkles size={18} />} onClick={() => navigate('/ai-generate')}>AI 生成图案</Button><Button variant="secondary" icon={<ImageUp size={18} />} onClick={() => navigate('/convert')}>上传图片转图纸</Button></div>
      </section>
      <section className="hero-visual" aria-label="柴犬图片转拼豆图纸示意">
        <div className="visual-blob blob-one" /><div className="visual-blob blob-two" />
        <div className="source-card"><span className="card-label">灵感草图</span><div className="soft-illustration"><span>🐕</span><i /><i /><i /></div><footer><span>柴犬挂饰</span><small>AI 创意图</small></footer></div>
        <div className="transform-badge"><ArrowRight size={20} /></div>
        <div className="pattern-card"><div className="pattern-card-head"><span className="card-label">拼豆图纸</span><span>52×52</span></div><BeadGrid motif="dog" size={18} /><footer><span><i style={{ background: '#9B5B36' }} /><i style={{ background: '#E8874A' }} /><i style={{ background: '#F7EEDC' }} /><i style={{ background: '#30353A' }} /></span><strong>14 色 · 963 颗</strong></footer></div>
        <div className="floating-note"><Grid3X3 size={16} /><span><small>已匹配色卡</small><strong>Mard · M23</strong></span></div>
      </section>
    </ResponsivePageContainer>

    <ResponsivePageContainer className="section-block">
      <div className="section-heading"><div><span className="eyebrow">核心能力</span><h2>每一步，都更接近亲手完成</h2></div></div>
      <div className="capability-grid">{capabilities.map((capability) => { const { icon: Icon, title, copy, accent } = capability; return <article key={title} className={`capability-card accent-${accent}`}><span className="capability-icon"><Icon /></span><h3>{title}</h3><p>{copy}</p><button type="button" className="quiet-link" onClick={() => setActiveCapability(capability)} aria-haspopup="dialog">了解这一步 <ArrowRight size={15} /></button></article>; })}</div>
    </ResponsivePageContainer>

    <section className="flow-band"><ResponsivePageContainer><div className="section-heading light"><div><span className="eyebrow">使用流程</span><h2>四步完成一件拼豆作品</h2></div></div><div className="flow-steps">{['产生灵感', '生成或上传图片', '编辑拼豆图纸', '制作与导出'].map((step, index) => <div key={step}><span>{index + 1}</span><strong>{step}</strong>{index < 3 && <ArrowRight />}</div>)}</div></ResponsivePageContainer></section>

    <ResponsivePageContainer className="section-block examples-section">
      <div className="section-heading"><div><span className="eyebrow">示例作品</span><h2>从这里开始你的下一件作品</h2></div><Button variant="ghost" onClick={() => navigate('/works')}>查看我的作品 <ArrowRight size={16} /></Button></div>
      <div className="example-grid">{seedWorks.map((work) => <WorkCard key={work.id} work={work} compact />)}</div>
    </ResponsivePageContainer>
    {activeCapability && <Modal open title={activeCapability.title} onClose={() => setActiveCapability(null)} actions={<><Button variant="ghost" onClick={() => setActiveCapability(null)}>先看看</Button><Button onClick={() => { setActiveCapability(null); navigate(activeCapability.route); }}>{activeCapability.cta} <ArrowRight size={16} /></Button></>}><p>{activeCapability.detail}</p><ul className="capability-detail-list">{activeCapability.points.map((point) => <li key={point}>{point}</li>)}</ul></Modal>}
  </main>;
}
