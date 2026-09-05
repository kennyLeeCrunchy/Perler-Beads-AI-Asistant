import Taro from '@tarojs/taro'
import type { Work } from '../shared/types'

const STORAGE_KEY = 'pindou.works.v1'

const isWork = (value: unknown): value is Work => {
  if (!value || typeof value !== 'object') return false
  const work = value as Work
  return typeof work.id === 'string' && typeof work.name === 'string' &&
    Number.isInteger(work.width) && Number.isInteger(work.height) && Array.isArray(work.cells)
}

const normalize = (work: Work): Work => ({
  ...work,
  cells: work.cells.map(row => row.map(cell => typeof cell === 'string' ? cell : null)),
  palette: Array.isArray(work.palette) ? work.palette : [],
  completedCells: Array.isArray(work.completedCells) ? work.completedCells : [],
  progress: getWorkProgress(work),
})

export function getWorks(): Work[] {
  try {
    const data = Taro.getStorageSync<unknown>(STORAGE_KEY)
    return (Array.isArray(data) ? data.filter(isWork).map(normalize) : [])
      .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
  } catch {
    return []
  }
}

export function getWork(id: string): Work | undefined {
  return getWorks().find(work => work.id === id)
}

export function saveWork(work: Work): Work {
  const next = normalize({ ...work, updatedAt: new Date().toISOString() })
  const works = getWorks()
  const index = works.findIndex(item => item.id === next.id)
  if (index >= 0) works[index] = next
  else works.unshift(next)
  Taro.setStorageSync(STORAGE_KEY, works)
  return next
}

export function createWork(input: Omit<Work, 'id' | 'createdAt' | 'updatedAt' | 'progress'>): Work {
  const now = new Date().toISOString()
  return saveWork({
    ...input,
    id: `work_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    createdAt: now,
    updatedAt: now,
    progress: 0,
  })
}

export function renameWork(id: string, name: string): Work | undefined {
  const work = getWork(id)
  const trimmed = name.trim().slice(0, 30)
  return work && trimmed ? saveWork({ ...work, name: trimmed }) : undefined
}

export function deleteWork(id: string): void {
  Taro.setStorageSync(STORAGE_KEY, getWorks().filter(work => work.id !== id))
}

export function cellKey(row: number, column: number): string {
  return `${row}:${column}`
}

export function getWorkProgress(work: Pick<Work, 'cells' | 'completedCells'>): number {
  const required = work.cells.flatMap((row, rowIndex) => row
    .map((cell, columnIndex) => cell ? cellKey(rowIndex, columnIndex) : '')
    .filter(Boolean))
  if (!required.length) return 0
  const completed = new Set(work.completedCells || [])
  return Math.round(required.filter(key => completed.has(key)).length / required.length * 100)
}
