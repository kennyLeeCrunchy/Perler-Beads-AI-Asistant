import { ScrollView, Text, View } from '@tarojs/components'
import type { PatternResult } from '../../shared/types'
import './index.scss'

export default function PatternGrid({ pattern }: { pattern: PatternResult }) {
  const colorMap = new Map(pattern.counts.map(item => [item.code, item.hex]))
  const cellSize = Math.max(10, Math.min(22, Math.floor(620 / pattern.width)))
  return <ScrollView scrollX scrollY className='pattern-grid-scroll' enhanced>
    <View className='pattern-grid' style={{ width: `${pattern.width * cellSize}rpx` }}>
      {pattern.cells.map((row, rowIndex) => <View className='pattern-grid__row' key={`r-${rowIndex}`}>
        {row.map((code, columnIndex) => <View
          className='pattern-grid__cell'
          key={`${rowIndex}-${columnIndex}`}
          style={{ width: `${cellSize}rpx`, height: `${cellSize}rpx`, backgroundColor: code ? colorMap.get(code) || '#fff' : 'transparent' }}
        >{cellSize >= 20 && code && <Text>{code}</Text>}</View>)}
      </View>)}
    </View>
  </ScrollView>
}
