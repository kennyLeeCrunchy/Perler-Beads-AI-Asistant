import Taro, { useLoad } from '@tarojs/taro'
import { Button, ScrollView, Text, View } from '@tarojs/components'
import { useState } from 'react'
import type { Work } from '../../shared/types'
import { cellKey, getWork, getWorkProgress, saveWork } from '../../store/works'
import './index.scss'

export default function MakePage() {
  const [work, setWork] = useState<Work>()
  useLoad(({ id }) => setWork(id ? getWork(id) : undefined))
  if (!work) return <View className='make state'>作品不存在或已被删除</View>
  const completed = new Set(work.completedCells || [])
  const total = work.cells.flat().filter(Boolean).length
  const done = work.cells.reduce((sum, row, r) => sum + row.filter((cell, c) => cell && completed.has(cellKey(r, c))).length, 0)
  const progress = getWorkProgress(work)
  const toggle = (r: number, c: number) => {
    if (!work.cells[r][c]) return
    const key = cellKey(r, c), next = new Set(completed)
    next.has(key) ? next.delete(key) : next.add(key)
    setWork(saveWork({ ...work, completedCells: [...next], status: next.size >= total ? 'completed' : 'draft' }))
  }
  return <View className='make'>
    <Text className='title'>{work.name}</Text><Text className='muted'>点按已完成的豆子，进度会自动保存</Text>
    <View className='summary'><Text className='percent'>{progress}%</Text><Text>{done} / {total} 颗</Text><View className='bar'><View style={{ width: `${progress}%` }} /></View></View>
    <ScrollView scrollX scrollY className='board'><View className='grid' style={{ width: `${work.width * 42}rpx` }}>{work.cells.map((row, r) => row.map((cell, c) => <View key={`${r}-${c}`} className={`cell ${completed.has(cellKey(r,c)) ? 'done' : ''} ${cell ? '' : 'blank'}`} style={{ background: work.palette.find(item => item.code === cell)?.hex || '#fff' }} onClick={() => toggle(r,c)}><Text>{completed.has(cellKey(r,c)) ? '✓' : cell || ''}</Text></View>))}</View></ScrollView>
    {progress === 100 && <View className='complete'>🎉 图纸已全部完成</View>}
    <Button className='reset' disabled={!done} onClick={() => Taro.showModal({ title:'重置制作进度？', content:'图纸内容不会被删除。' }).then(result => result.confirm && setWork(saveWork({ ...work, completedCells:[], status:'draft' })))}>重置进度</Button>
  </View>
}
