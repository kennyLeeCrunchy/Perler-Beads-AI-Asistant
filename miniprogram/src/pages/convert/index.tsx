import { Button, Image, Picker, Switch, Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState } from 'react'
import StatusPanel from '../../components/StatusPanel'
import { generatePattern } from '../../services/api'
import type { BeadBrand } from '../../shared/types'
import { toUserMessage } from '../../utils/error'
import { saveLatestPattern } from '../../utils/pattern'
import './index.scss'

const sizes = [52, 78, 104]
const colorOptions = [12, 24, 36, 0]

export default function ConvertPage() {
  const [filePath, setFilePath] = useState('')
  const [fileSize, setFileSize] = useState(0)
  const [brand, setBrand] = useState<BeadBrand>('Artkal')
  const [size, setSize] = useState(52)
  const [maxColors, setMaxColors] = useState(24)
  const [similarity, setSimilarity] = useState(18)
  const [removeBackground, setRemoveBackground] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const chooseImage = async () => {
    try {
      const result = await Taro.chooseMedia({ count: 1, mediaType: ['image'], sourceType: ['album', 'camera'], sizeType: ['compressed'] })
      const file = result.tempFiles[0]
      if (!file) return
      if (file.size > 10 * 1024 * 1024) {
        setError('图片不能超过 10MB，请压缩后重试')
        return
      }
      setFilePath(file.tempFilePath)
      setFileSize(file.size)
      setError('')
    } catch (reason) {
      const message = toUserMessage(reason)
      if (message) setError(message)
    }
  }

  const submit = async () => {
    if (!filePath || loading) return
    setLoading(true)
    setError('')
    try {
      const pattern = await generatePattern({
        filePath, brand, width: size, height: size, maxColors,
        similarityThreshold: similarity, useTransparentMask: removeBackground,
      })
      saveLatestPattern(pattern)
      await Taro.navigateTo({ url: '/pages/preview/index' })
    } catch (reason) {
      setError(toUserMessage(reason))
    } finally {
      setLoading(false)
    }
  }

  return <View className='convert-page'>
    <View className='convert-page__intro'>
      <Text className='convert-page__eyebrow'>三步完成</Text>
      <Text className='convert-page__title'>把照片变成拼豆图纸</Text>
      <Text className='convert-page__subtitle'>选择图片、设置尺寸，系统会自动匹配色号并统计数量。</Text>
    </View>

    <View className='convert-card'>
      <Text className='section-title'>1. 选择图片</Text>
      {filePath
        ? <View className='image-preview' onClick={chooseImage}><Image src={filePath} mode='aspectFit' /><Text>点击更换 · {(fileSize / 1024 / 1024).toFixed(1)}MB</Text></View>
        : <Button className='upload-button' onClick={chooseImage}>从相册选择或拍照</Button>}
      <Text className='field-tip'>支持 JPG、PNG、WEBP，单张不超过 10MB。图片仅用于生成图纸。</Text>
    </View>

    <View className='convert-card'>
      <Text className='section-title'>2. 设置图纸参数</Text>
      <Text className='field-label'>色卡品牌</Text>
      <View className='segments'>{(['Artkal', 'Mard'] as BeadBrand[]).map(item => <Button key={item} className={brand === item ? 'active' : ''} onClick={() => setBrand(item)}>{item}</Button>)}</View>
      <Text className='field-label'>图纸尺寸</Text>
      <View className='segments'>{sizes.map(item => <Button key={item} className={size === item ? 'active' : ''} onClick={() => setSize(item)}>{item}×{item}</Button>)}</View>
      <View className='picker-row'><View><Text className='field-label'>最大颜色数</Text><Text className='field-tip'>颜色更少更容易制作</Text></View><Picker mode='selector' range={colorOptions.map(v => v ? `${v} 色` : '自动')} onChange={event => setMaxColors(colorOptions[Number(event.detail.value)])}><Text>{maxColors ? `${maxColors} 色` : '自动'} ›</Text></Picker></View>
      <Text className='field-label'>相似色合并</Text>
      <View className='segments'>{[{ v: 0, n: '关闭' }, { v: 18, n: '标准' }, { v: 28, n: '强' }].map(item => <Button key={item.v} className={similarity === item.v ? 'active' : ''} onClick={() => setSimilarity(item.v)}>{item.n}</Button>)}</View>
      <View className='switch-row'><View><Text className='field-label'>自动移除背景</Text><Text className='field-tip'>适合主体清晰、背景干净的图片</Text></View><Switch color='#247653' checked={removeBackground} onChange={event => setRemoveBackground(event.detail.value)} /></View>
    </View>

    {loading && <StatusPanel kind='loading' title='正在生成图纸' description='大尺寸图片可能需要约一分钟，请不要关闭小程序。' />}
    {error && <StatusPanel kind='error' title='未能完成操作' description={error} actionText={filePath ? '重新生成' : '重新选择'} onAction={filePath ? submit : chooseImage} />}
    <Button className='primary-action' disabled={!filePath || loading} loading={loading} onClick={submit}>{loading ? '正在处理…' : '生成图纸'}</Button>
  </View>
}
