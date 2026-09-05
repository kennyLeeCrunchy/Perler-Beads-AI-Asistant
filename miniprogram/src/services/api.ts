import Taro from '@tarojs/taro'
import type { BeadBrand, PatternResult } from '../shared/types'

const configuredBase = (process.env.TARO_APP_API_BASE_URL || '').trim().replace(/\/$/, '')

export const API_BASE_URL = configuredBase

export interface GeneratePatternInput {
  filePath: string
  brand: BeadBrand
  width: number
  height: number
  maxColors: number
  similarityThreshold: number
  useTransparentMask: boolean
}

interface ApiErrorPayload { detail?: string }

function parsePayload<T>(data: string | T): T {
  if (typeof data !== 'string') return data
  try {
    return JSON.parse(data) as T
  } catch {
    throw new Error('服务器返回了无法识别的数据')
  }
}

function readableError(data: string, statusCode: number) {
  try {
    const payload = JSON.parse(data) as ApiErrorPayload
    return payload.detail || `请求失败（${statusCode}）`
  } catch {
    return `请求失败（${statusCode}）`
  }
}

export async function generatePattern(input: GeneratePatternInput): Promise<PatternResult> {
  if (!API_BASE_URL) {
    throw new Error('服务地址尚未配置，请联系管理员')
  }

  const result = await Taro.uploadFile({
    url: `${API_BASE_URL}/api/pattern/generate`,
    filePath: input.filePath,
    name: 'image',
    formData: {
      brand: input.brand,
      width: String(input.width),
      height: String(input.height),
      preset: '221',
      max_colors: String(input.maxColors),
      similarity_threshold: String(input.similarityThreshold),
      use_transparent_mask: String(input.useTransparentMask),
    },
    timeout: 120000,
  })

  if (result.statusCode < 200 || result.statusCode >= 300) {
    throw new Error(readableError(result.data, result.statusCode))
  }
  return parsePayload<PatternResult>(result.data)
}
