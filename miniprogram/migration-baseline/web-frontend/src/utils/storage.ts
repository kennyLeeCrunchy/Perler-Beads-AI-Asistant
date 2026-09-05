import { seedWorks } from '../demo/seedData';
import type { Work } from '../types';

const STORAGE_KEY = 'perler-assistant-works-v1';

export function loadWorks(): Work[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return seedWorks;
    const parsed = JSON.parse(raw) as Work[];
    return Array.isArray(parsed) ? parsed : seedWorks;
  } catch {
    return seedWorks;
  }
}

export function saveWorks(works: Work[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(works));
}

export function findWork(id?: string): Work | undefined {
  if (!id) return undefined;
  return loadWorks().find((work) => work.id === id)
    ?? seedWorks.find((work) => work.id === id);
}

export function upsertWork(work: Work) {
  const works = loadWorks();
  const index = works.findIndex((item) => item.id === work.id);
  const next = index >= 0 ? works.map((item) => (item.id === work.id ? work : item)) : [work, ...works];
  saveWorks(next);
  return next;
}

export function deleteWork(id: string) {
  const next = loadWorks().filter((work) => work.id !== id);
  saveWorks(next);
  return next;
}
