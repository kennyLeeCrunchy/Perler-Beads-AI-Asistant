import Taro from '@tarojs/taro'
import type { PatternResult } from '../shared/types'

const RESULT_KEY = 'latest-pattern-result'

export function saveLatestPattern(result: PatternResult) {
  Taro.setStorageSync(RESULT_KEY, result)
}

export function getLatestPattern(): PatternResult | undefined {
  const value = Taro.getStorageSync<PatternResult | ''>(RESULT_KEY)
  return value || undefined
}

export function totalBeads(result: PatternResult) {
  return result.counts.reduce((sum, item) => sum + item.count, 0)
}
