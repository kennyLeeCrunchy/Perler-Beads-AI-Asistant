import { Home, ImageUp, Menu, Sparkles, X, FolderHeart } from 'lucide-react';
import { NavLink, useLocation } from 'react-router-dom';
import { useState } from 'react';
import { IconButton } from './IconButton';

const navItems = [
  { to: '/ai-generate', label: 'AI 生图', icon: Sparkles },
  { to: '/convert', label: '图片转图纸', icon: ImageUp },
  { to: '/works', label: '我的作品', icon: FolderHeart },
];

function Brand() {
  return (
    <div className="brand">
      <NavLink to="/" className="brand-mark-wrap" aria-label="返回首页">
        <img src="/perlabo-red-bead-logo.png" alt="" className="brand-mark" />
      </NavLink>
      <span className="brand-name">Perlabo拼豆实验室</span>
    </div>
  );
}

export function Navbar() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const focusMode = location.pathname.startsWith('/editor/') || location.pathname.startsWith('/make/');

  return (
    <>
      <header className={`navbar ${focusMode ? 'navbar-focus' : ''}`}>
        <Brand />
        <nav className="desktop-nav" aria-label="主导航">
          {navItems.map(({ to, label }) => <NavLink key={to} to={to}>{label}</NavLink>)}
        </nav>
        <div className="account-area">
          <IconButton className="menu-button" aria-label="打开导航" onClick={() => setOpen(true)}><Menu size={22} /></IconButton>
        </div>
      </header>

      <div className={`mobile-menu-backdrop ${open ? 'is-open' : ''}`} onClick={() => setOpen(false)} />
      <aside className={`mobile-menu ${open ? 'is-open' : ''}`} aria-hidden={!open}>
        <div className="mobile-menu-head"><strong>前往页面</strong><IconButton aria-label="关闭导航" onClick={() => setOpen(false)}><X size={22} /></IconButton></div>
        <NavLink to="/" onClick={() => setOpen(false)}><Home size={20} />首页</NavLink>
        {navItems.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} onClick={() => setOpen(false)}><Icon size={20} />{label}</NavLink>)}
      </aside>

      {!focusMode && (
        <nav className="mobile-bottom-nav" aria-label="移动端主导航">
          <NavLink to="/"><Home size={20} /><span>首页</span></NavLink>
          {navItems.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to}><Icon size={20} /><span>{label.replace('图片转图纸', '转图纸')}</span></NavLink>)}
        </nav>
      )}
    </>
  );
}
