import { CheckCircle2 } from 'lucide-react';
import { useEffect, useState } from 'react';

export function ToastHost() {
  const [message, setMessage] = useState('');
  useEffect(() => {
    let timer = 0;
    const handler = (event: Event) => {
      setMessage((event as CustomEvent<string>).detail);
      window.clearTimeout(timer);
      timer = window.setTimeout(() => setMessage(''), 2600);
    };
    window.addEventListener('app-toast', handler);
    return () => { window.removeEventListener('app-toast', handler); window.clearTimeout(timer); };
  }, []);
  return <div className={`toast ${message ? 'is-visible' : ''}`}><CheckCircle2 size={18} />{message}</div>;
}

export function showToast(message: string) {
  window.dispatchEvent(new CustomEvent('app-toast', { detail: message }));
}
