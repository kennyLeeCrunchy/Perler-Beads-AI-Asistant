import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { ToastHost } from './components/Toast';
import { AIGeneratePage } from './pages/AIGeneratePage';
import { ConvertPage } from './pages/ConvertPage';
import { EditorPage } from './pages/EditorPage';
import { HomePage } from './pages/HomePage';
import { MakePage } from './pages/MakePage';
import { WorksPage } from './pages/WorksPage';

export default function App() {
  const location = useLocation();
  const focus = location.pathname.startsWith('/editor/') || location.pathname.startsWith('/make/');
  return <div className={`app-shell ${focus ? 'focus-shell' : ''}`}>
    <Navbar />
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/ai-generate" element={<AIGeneratePage />} />
      <Route path="/convert" element={<ConvertPage />} />
      <Route path="/editor/:id" element={<EditorPage />} />
      <Route path="/make/:id" element={<MakePage />} />
      <Route path="/works" element={<WorksPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    <ToastHost />
  </div>;
}
