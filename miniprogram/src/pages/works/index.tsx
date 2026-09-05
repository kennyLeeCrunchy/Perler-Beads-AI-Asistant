import { useDidShow } from '@tarojs/taro'
import Taro from '@tarojs/taro'
import { Button, Text, View } from '@tarojs/components'
import { useState } from 'react'
import type { Work } from '../../shared/types'
import { deleteWork, getWorks, renameWork } from '../../store/works'
import './index.scss'

export default function WorksPage() {
  const [works, setWorks] = useState<Work[]>([])
  const reload = () => setWorks(getWorks())
  useDidShow(reload)

  const rename = (work: Work) => Taro.showModal({
    title: '重命名作品', editable: true, placeholderText: work.name, content: work.name,
  } as Parameters<typeof Taro.showModal>[0]).then(result => {
    const nextName = (result as typeof result & { content?: string }).content?.trim()
    if (result.confirm && nextName) {
      renameWork(work.id, nextName)
      reload()
    }
  })

  const remove = (work: Work) => Taro.showModal({
    title: '删除作品？', content: `“${work.name}”删除后无法恢复。`, confirmColor: '#d14343',
  }).then(result => {
    if (result.confirm) { deleteWork(work.id); reload() }
  })

  if (!works.length) return <View className='works empty'>
    <Text className='empty-icon'>◇</Text><Text className='empty-title'>还没有作品</Text>
    <Text className='muted'>从首页选择图片生成图纸，作品会自动保存在这里。</Text>
    <Button className='primary' onClick={() => Taro.switchTab({ url: '/pages/home/index' })}>去创建</Button>
  </View>

  return <View className='works'>
    <View className='heading'><Text className='title'>我的作品</Text><Text className='muted'>{works.length} 个本地作品</Text></View>
    {works.map(work => <View className='card' key={work.id}>
      <View className='preview' onClick={() => Taro.navigateTo({ url: `/pages/editor/index?id=${work.id}` })}>
        <Text>{work.width} × {work.height}</Text>
      </View>
      <View className='meta'>
        <Text className='name'>{work.name}</Text>
        <Text className='muted'>{work.brand} · {new Date(work.updatedAt).toLocaleDateString()}</Text>
        <View className='progress'><View className='progress-fill' style={{ width: `${work.progress}%` }} /></View>
        <Text className='muted'>制作进度 {work.progress}%</Text>
        <View className='actions'>
          <Text onClick={() => rename(work)}>重命名</Text><Text onClick={() => remove(work)}>删除</Text>
          <Button size='mini' className='open' onClick={() => Taro.navigateTo({ url: `/pages/editor/index?id=${work.id}` })}>打开</Button>
        </View>
      </View>
    </View>)}
  </View>
}
