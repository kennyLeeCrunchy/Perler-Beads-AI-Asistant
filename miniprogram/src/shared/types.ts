export type WorkStatus = 'draft' | 'completed'

export type BeadBrand = 'Mard' | 'Artkal'

export interface BeadColor {
  brand: BeadBrand
  code: string
  name: string
  hex: string
  count: number
  remaining: number
}

export interface PatternCount {
  code: string
  count: number
  hex: string
  name: string
}

export interface PatternResult {
  pattern_id: string
  brand: BeadBrand
  width: number
  height: number
  cells: Array<Array<string | null>>
  counts: PatternCount[]
  preview_data_url: string
}

/** A locally persisted work. Cloud sync can extend this shape without migration. */
export interface Work {
  id: string
  name: string
  width: number
  height: number
  brand: BeadBrand
  status: WorkStatus
  createdAt: string
  updatedAt: string
  progress: number
  palette: BeadColor[]
  cells: Array<Array<string | null>>
  completedCells?: string[]
  patternId?: string
  previewDataUrl?: string
  sourceImagePath?: string
}
