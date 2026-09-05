import { Button, Image, ScrollView, Text, View } from '@tarojs/components'
import Taro, { useDidShow } from '@tarojs/taro'
import { useState } from 'react'
import PatternGrid from '../../components/PatternGrid'
import StatusPanel from '../../components/StatusPanel'
import type { PatternResult } from '../../shared/types'
import { toUserMessage } from '../../utils/error'
import { getLatestPattern, totalBeads } from '../../utils/pattern'
import './index.scss'

export default function PreviewPage() {
  const [pattern, setPattern] = useState<PatternResult>()
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useDidShow(() => setPattern(getLatestPattern()))

  const savePreview = async () => {
    if (!pattern?.preview_data_url || saving) return
    setSaving(true)
    setError('')
    try {
      const match = pattern.preview_data_url.match(/^data:image\/png;base64,(.+)$/)
      if (!match) throw new Error('当前结果不支持保存')
      const filePath = `${Taro.env.USER_DATA_PATH}/pattern-${pattern.pattern_id}.png`
      Taro.getFileSystemManager().writeFileSync(filePath, match[1], 'base64')
      await Taro.saveImageToPhotosAlbum({ filePath })
      await Taro.showToast({ title: '已保存到相册', icon: 'success' })
    } catch (reason) {
      const message = toUserMessage(reason)
      setError(/auth deny|authorize/i.test(String((reason as { errMsg?: string })?.errMsg)) ? '请在小程序设置中允许保存到相册' : message)
    } finally {
      setSaving(false)
    }
  }

  if (!pattern) return <View className='preview-page'><StatusPanel kind='empty' title='暂无可预览的图纸' description='请先选择图片并完成转换。' actionText='去生成' onAction={() => Taro.redirectTo({ url: '/pages/convert/index' })} /></View>

  return <View className='preview-page'>
    <View className='preview-heading'><Text className='preview-heading__tag'>生成完成</Text><Text className='preview-heading__title'>{pattern.width}×{pattern.height} 拼豆图纸</Text><Text className='preview-heading__meta'>{pattern.brand} 色卡 · {pattern.counts.length} 种颜色 · {totalBeads(pattern)} 颗</Text></View>
    <View className='preview-card'>
      <PatternGrid pattern={pattern} />
      <Text className='preview-hint'>可双向滑动查看图纸；小格中的文字为色号。</Text>
    </View>
    <View className='preview-card'>
      <Text className='section-title'>用量清单</Text>
      <ScrollView scrollY className='palette-list'>
        {pattern.counts.map(item => <View className='palette-item' key={item.code}><View className='palette-swatch' style={{ backgroundColor: item.hex }} /><View className='palette-name'><Text>{item.code}</Text><Text>{item.name}</Text></View><Text className='palette-count'>{item.count} 颗</Text></View>)}
      </ScrollView>
    </View>
    {pattern.preview_data_url && <View className='preview-card'><Text className='section-title'>成品预览</Text><Image className='result-image' src={pattern.preview_data_url} mode='widthFix' /></View>}
    {error && <StatusPanel kind='error' title='保存失败' description={error} />}
    <View className='preview-actions'><Button onClick={() => Taro.navigateBack()}>调整参数</Button><Button className='primary' loading={saving} onClick={savePreview}>{saving ? '保存中…' : '保存到相册'}</Button></View>
  </View>
}
