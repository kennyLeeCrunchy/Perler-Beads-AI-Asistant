import { ImagePlus, UploadCloud, X } from 'lucide-react';
import { useRef, useState } from 'react';
import { Button } from './Button';

export function UploadArea({ compact = false, onUploaded, onRemoved }: { compact?: boolean; onUploaded?: (file: File) => void; onRemoved?: () => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState('');
  const choose = (file?: File) => {
    if (!file) return;
    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      window.dispatchEvent(new CustomEvent('app-toast', { detail: '仅支持 JPG、PNG；请重新选择图片' }));
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      window.dispatchEvent(new CustomEvent('app-toast', { detail: '图片超过 10MB；请压缩后重新上传' }));
      return;
    }
    setFileName(file.name);
    onUploaded?.(file);
  };
  return (
    <div className={`upload-area ${compact ? 'compact' : ''}`} onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); choose(e.dataTransfer.files[0]); }}>
      <input ref={input} hidden type="file" accept="image/png,image/jpeg" onChange={(e) => choose(e.target.files?.[0])} />
      {fileName ? (
        <div className="uploaded-preview"><ImagePlus size={32} /><div><strong>{fileName}</strong><span>图片已就绪 · 可继续设置参数</span></div><button aria-label="移除图片" onClick={() => { setFileName(''); onRemoved?.(); }}><X size={18} /></button></div>
      ) : (
        <><span className="upload-icon"><UploadCloud /></span><strong>拖拽图片到这里，或点击选择</strong><span>支持 JPG、PNG，最大 10MB</span><Button variant="secondary" type="button" onClick={() => input.current?.click()}>选择图片</Button></>
      )}
    </div>
  );
}
