import { Copy, Download, Edit3, Plus, Search, Trash2 } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/Button';
import { Drawer } from '../components/Drawer';
import { Modal } from '../components/Modal';
import { PatternSummary } from '../components/PatternSummary';
import { ResponsivePageContainer } from '../components/ResponsivePageContainer';
import { showToast } from '../components/Toast';
import { WorkCard } from '../components/WorkCard';
import { BeadGrid } from '../components/BeadGrid';
import type { Work, WorkStatus } from '../types';
import { deleteWork, loadWorks, saveWorks } from '../utils/storage';

export function WorksPage() {
  const navigate = useNavigate();
  const [works, setWorks] = useState(loadWorks);
  const [filter, setFilter] = useState<'全部' | WorkStatus>('全部');
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState('最近编辑');
  const [active, setActive] = useState<Work | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const filtered = useMemo(() => works.filter((work) => (filter === '全部' || work.status === filter) && work.name.includes(query)).sort((a, b) => sort === '名称' ? a.name.localeCompare(b.name, 'zh-CN') : +new Date(b.updatedAt) - +new Date(a.updatedAt)), [works, filter, query, sort]);
  const duplicate = () => { if (!active) return; const next = { ...active, id: `${active.id}-${Date.now()}`, name: `${active.name} 副本`, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(), status: '草稿' as const }; const list = [next, ...works]; setWorks(list); saveWorks(list); setActive(null); showToast('作品已复制，可继续编辑'); };
  const remove = () => { if (!active) return; setWorks(deleteWork(active.id)); setConfirmDelete(false); setActive(null); showToast('作品已删除'); };
  return <ResponsivePageContainer className="page-section works-page">
    <header className="works-heading"><div><span className="eyebrow">保存在当前浏览器</span><h1>我的作品</h1><p>继续编辑草稿，或带着完成的图纸开始制作。</p></div><Button icon={<Plus size={18} />} onClick={() => navigate('/ai-generate')}>新建作品</Button></header>
    <div className="works-toolbar panel-card"><div className="filter-chips">{(['全部', '草稿', '已完成'] as const).map((item) => <button key={item} className={filter === item ? 'is-active' : ''} onClick={() => setFilter(item)}>{item}<span>{item === '全部' ? works.length : works.filter((work) => work.status === item).length}</span></button>)}</div><div className="toolbar-fields"><label className="search-field"><Search size={17} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="搜索作品名称" /></label><select value={sort} onChange={(e) => setSort(e.target.value)}><option>最近编辑</option><option>最近创建</option><option>名称</option><option>图纸尺寸</option></select></div></div>
    <div className="local-note">作品仅保存在当前浏览器。清理浏览器数据后，作品可能无法恢复。</div>
    <div className="works-grid">{filtered.map((work) => <WorkCard key={work.id} work={work} onMore={setActive} />)}</div>
    {!filtered.length && <div className="empty-works"><h2>还没有保存的拼豆作品</h2><p>从 AI 灵感或一张照片开始吧。</p><div><Button onClick={() => navigate('/ai-generate')}>AI 生成图案</Button><Button variant="secondary" onClick={() => navigate('/convert')}>上传图片转图纸</Button></div></div>}
    <Drawer open={!!active} title="作品详情" onClose={() => setActive(null)}>{active && <div className="work-detail"><div className="detail-preview">{active.grid.length && active.gridSize ? <BeadGrid size={active.gridSize} cells={active.grid} colors={active.palette} /> : active.previewDataUrl ? <img src={active.previewDataUrl} alt="" /> : <BeadGrid motif={active.motif} size={20} />}</div><div><span className={`status-pill ${active.status === '已完成' ? 'done' : ''}`}>{active.status}</span><h2>{active.name}</h2><PatternSummary work={active} compact /><p>最后编辑：{new Date(active.updatedAt).toLocaleDateString('zh-CN')}</p></div><div className="detail-actions"><Button onClick={() => navigate(`/editor/${active.id}`)}>继续编辑</Button><Button variant="secondary" onClick={() => navigate(`/make/${active.id}`)}>制作辅助</Button></div><div className="drawer-menu"><button onClick={() => navigate(`/make/${active.id}`)}><Download />导出图纸</button><button onClick={duplicate}><Copy />复制作品</button><button onClick={() => showToast('进入编辑器后可直接修改作品名')}><Edit3 />重命名</button><button className="danger" onClick={() => setConfirmDelete(true)}><Trash2 />删除作品</button></div></div>}</Drawer>
    <Modal open={confirmDelete} title="确认删除作品？" onClose={() => setConfirmDelete(false)} actions={<><Button variant="ghost" onClick={() => setConfirmDelete(false)}>取消</Button><Button variant="danger" onClick={remove}>确认删除</Button></>}><p>删除后无法恢复。你也可以先导出图纸，再进行删除。</p></Modal>
  </ResponsivePageContainer>;
}
