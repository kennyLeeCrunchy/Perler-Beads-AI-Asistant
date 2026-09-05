export interface AiImageResult {
  source_path: string;
  raw_source_path: string;
  image_url: string;
  raw_image_url: string;
  prompt: string;
  final_prompt: string;
  transparent_irregular: boolean;
  mask_method: string | null;
  foreground_ratio: number | null;
}

export interface PatternCount {
  code: string;
  count: number;
  hex: string;
  name: string;
}

export interface PatternResult {
  pattern_id: string;
  brand: 'Artkal' | 'Mard';
  width: number;
  height: number;
  cells: Array<Array<string | null>>;
  counts: PatternCount[];
  preview_data_url: string;
}

const configuredBase = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim().replace(/\/$/, '');
export const API_BASE_URL = configuredBase ?? '';

function apiUrl(path: string) {
  return `${API_BASE_URL}${path}`;
}

async function readError(response: Response) {
  try {
    const payload = await response.json() as { detail?: string };
    return payload.detail || `请求失败（${response.status}）`;
  } catch {
    return `请求失败（${response.status}）`;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), init);
  if (!response.ok) throw new Error(await readError(response));
  return response.json() as Promise<T>;
}

export function resolveApiMediaUrl(path: string) {
  if (/^https?:\/\//i.test(path) || path.startsWith('data:')) return path;
  return apiUrl(path.startsWith('/') ? path : `/${path}`);
}

export function generateAiImage(prompt: string, transparentIrregular: boolean) {
  return request<AiImageResult>('/api/ai/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, transparent_irregular: transparentIrregular }),
  });
}

export function generatePattern(input: {
  image?: File;
  sourcePath?: string;
  brand: 'Artkal' | 'Mard';
  width: number;
  height: number;
  preset?: string;
  maxColors: number;
  similarityThreshold: number;
  useTransparentMask: boolean;
}) {
  const form = new FormData();
  if (input.image) form.append('image', input.image);
  if (input.sourcePath) form.append('source_path', input.sourcePath);
  form.append('brand', input.brand);
  form.append('width', String(input.width));
  form.append('height', String(input.height));
  form.append('preset', input.preset ?? '221');
  form.append('max_colors', String(input.maxColors));
  form.append('similarity_threshold', String(input.similarityThreshold));
  form.append('use_transparent_mask', String(input.useTransparentMask));
  return request<PatternResult>('/api/pattern/generate', { method: 'POST', body: form });
}

export async function exportPatternPng(payload: {
  patternId?: string;
  width: number;
  height: number;
  cells: Array<Array<string | null>>;
  colors: Array<{ code: string; hex: string; name: string }>;
}) {
  const response = await fetch(apiUrl('/api/export/png'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pattern_id: payload.patternId,
      width: payload.width,
      height: payload.height,
      cells: payload.cells,
      colors: payload.colors,
    }),
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.blob();
}
