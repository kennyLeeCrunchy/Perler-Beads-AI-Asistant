import Taro, { useLoad } from '@tarojs/taro'
import { Button, ScrollView, Text, View } from '@tarojs/components'
import { useState } from 'react'
import type { Work } from '../../shared/types'
import { getWork, saveWork } from '../../store/works'
import './index.scss'

export default function EditorPage() {
  const [work, setWork] = useState<Work>()
  const [history, setHistory] = useState<Work['cells'][]>([])
  const [color, setColor] = useState('')
  useLoad(({ id }) => {
    const found = id ? getWork(id) : undefined
    setWork(found)
    if (found) setColor(found.palette[0]?.code || found.cells.flat().find(Boolean) || '')
  })
  if (!work) return <View className='state'><Text>作品不存在或已被删除</Text><Button onClick={() => Taro.navigateBack()}>返回</Button></View>

  const paint = (row: number, column: number) => {
    if (!color) return
    const before = work.cells.map(line => [...line])
    const cells = work.cells.map(line => [...line])
    cells[row][column] = cells[row][column] === color ? null : color
    setHistory(items => [...items.slice(-19), before])
    setWork({ ...work, cells })
  }
  const undo = () => {
    const cells = history[history.length - 1]
    if (!cells) return
    setWork({ ...work, cells })
    setHistory(items => items.slice(0, -1))
  }
  const save = () => { setWork(saveWork(work)); Taro.showToast({ title: '草稿已保存', icon: 'success' }) }

  return <View className='editor'>
    <View className='editor-head'><View><Text className='editor-title'>{work.name}</Text><Text className='hint'>点击格子填色，再点一次清除</Text></View><Button size='mini' onClick={undo} disabled={!history.length}>撤销</Button></View>
    <ScrollView scrollX scrollY className='grid-scroll'>
      <View className='grid' style={{ width: `${work.width * 42}rpx` }}>
        {work.cells.map((row, r) => row.map((cell, c) => {
          const hex = work.palette.find(item => item.code === cell)?.hex || '#ffffff'
          return <View key={`${r}-${c}`} className='cell' style={{ background: hex }} onClick={() => paint(r, c)}><Text>{cell || ''}</Text></View>
        }))}
      </View>
    </ScrollView>
    <Text className='section-title'>当前颜色</Text>
    <ScrollView scrollX className='palette'><View className='palette-row'>{work.palette.map(item => <View key={item.code} className={`swatch ${color === item.code ? 'active' : ''}`} onClick={() => setColor(item.code)}><View className='dot' style={{ background: item.hex }} /><Text>{item.code}</Text></View>)}</View></ScrollView>
    <View className='bottom'><Button className='secondary' onClick={() => Taro.navigateTo({ url: `/pages/make/index?id=${work.id}` })}>制作辅助</Button><Button className='save' onClick={save}>保存草稿</Button></View>
  </View>
}
