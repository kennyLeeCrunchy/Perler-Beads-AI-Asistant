import Taro from '@tarojs/taro'
import { Button, Text, View } from '@tarojs/components'
import './index.scss'

export default function SettingsPage() {
  const clearLocalData = async () => {
    const result = await Taro.showModal({
      title: '清理本地数据',
      content: '将清除本机中的草稿和偏好设置。已保存到相册的图片不受影响。',
      confirmText: '确认清理',
      confirmColor: '#b74632',
    })
    if (!result.confirm) return
    try {
      Taro.clearStorageSync()
      await Taro.showToast({ title: '已清理', icon: 'success' })
    } catch {
      await Taro.showToast({ title: '清理失败，请重试', icon: 'none' })
    }
  }

  return (
    <View className='page-shell settings-page'>
      <View className='card setting-group'>
        <View className='setting-row' onClick={() => Taro.navigateTo({ url: '/pages/privacy/index' })}>
          <View>
            <Text className='setting-title'>隐私与数据说明</Text>
            <Text className='setting-description'>了解图片、作品和设备数据的使用方式</Text>
          </View>
          <Text className='chevron'>›</Text>
        </View>
      </View>
      <View className='card local-data'>
        <Text className='setting-title'>本地数据</Text>
        <Text className='setting-description block'>草稿和界面偏好仅保存在当前设备，可随时清理。</Text>
        <Button className='secondary-button clear-button' onClick={clearLocalData}>清理本地数据</Button>
      </View>
      <View className='review-note'>
        <Text className='review-note-title'>当前版本说明</Text>
        <Text className='setting-description block'>本版本仅提供图片转拼豆图纸、编辑与保存能力，不包含 AI 图片生成功能，也不提供公开内容发布或用户互动。</Text>
      </View>
      <Text className='version'>拼豆助手 0.1.0</Text>
    </View>
  )
}
