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

export interface CleanReferenceResult {
  clean_reference_id: string;
  task_id: string;
  model: string;
  algorithm_version: string;
  pipeline: string;
  ai_passes: number;
  source_type: string;
  confidence: number;
  mask_method: string | null;
  foreground_ratio: number | null;
  image_url: string;
  raw_image_url: string;
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
  quality?: {
    structure: { score: number; passed: boolean; feedback: string[] };
    color: { score: number; mean_delta_e: number; p90_delta_e: number; alpha_iou: number; feedback: string[] };
  };
}

export interface PatternBundleResult {
  brand: 'Artkal' | 'Mard';
  algorithm_version: string;
  pipeline: string;
  ai_passes: number;
  clean_reference_id: string | null;
  variants: PatternResult[];
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

export function cleanReference(input: {
  image: File;
  mode: 'auto' | 'subject' | 'scene';
  subjectTarget?: string;
  prompt?: string;
}) {
  const form = new FormData();
  form.append('image', input.image);
  form.append('mode', input.mode);
  form.append('subject_target', input.subjectTarget ?? '');
  form.append('prompt', input.prompt ?? '');
  return request<CleanReferenceResult>('/api/ai/clean-reference', { method: 'POST', body: form });
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

export function generatePatternBundle(input: {
  image?: File;
  sourcePath?: string;
  cleanReferenceId?: string;
  brand: 'Artkal' | 'Mard';
  preset?: string;
  maxColors: number;
  similarityThreshold: number;
  useTransparentMask: boolean;
}) {
  const form = new FormData();
  if (input.image) form.append('image', input.image);
  if (input.sourcePath) form.append('source_path', input.sourcePath);
  if (input.cleanReferenceId) form.append('clean_reference_id', input.cleanReferenceId);
  form.append('brand', input.brand);
  form.append('preset', input.preset ?? '221');
  form.append('max_colors', String(input.maxColors));
  form.append('similarity_threshold', String(input.similarityThreshold));
  form.append('use_transparent_mask', String(input.useTransparentMask));
  return request<PatternBundleResult>('/api/pattern/bundle', { method: 'POST', body: form });
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

export async function exportPatternPdf(payload: {
  patternId?: string;
  width: number;
  height: number;
  cells: Array<Array<string | null>>;
  colors: Array<{ code: string; hex: string; name: string }>;
}) {
  const response = await fetch(apiUrl('/api/export/pdf'), {
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
