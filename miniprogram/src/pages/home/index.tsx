import Taro from '@tarojs/taro'
import { Button, Text, View } from '@tarojs/components'
import './index.scss'

export default function HomePage() {
  const startConvert = () => Taro.navigateTo({ url: '/pages/convert/index' })

  return (
    <View className='page-shell home-page'>
      <View className='hero'>
        <Text className='eyebrow'>PERLABO · 拼豆助手</Text>
        <Text className='title'>把喜欢的图片，变成清晰的拼豆图纸</Text>
        <Text className='subtitle'>选择手机里的图片，调整尺寸和色卡，即可生成可编辑、可保存的图纸。</Text>
        <Button className='primary-button start-button' onClick={startConvert}>选择图片开始制作</Button>
        <Text className='privacy-tip'>仅在你主动操作时读取所选图片；首审版本不提供 AI 生图。</Text>
      </View>

      <View className='card steps'>
        <Text className='section-title'>三步完成</Text>
        {[
          ['01', '选择图片', '从相册选择一张清晰的图片'],
          ['02', '生成图纸', '设置网格尺寸并匹配拼豆色号'],
          ['03', '编辑保存', '微调格子后保存作品或图片'],
        ].map(([number, title, description]) => (
          <View className='step' key={number}>
            <Text className='step-number'>{number}</Text>
            <View className='step-copy'>
              <Text className='step-title'>{title}</Text>
              <Text className='step-description'>{description}</Text>
            </View>
          </View>
        ))}
      </View>
    </View>
  )
}
