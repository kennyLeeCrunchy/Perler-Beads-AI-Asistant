import { Text, View } from '@tarojs/components'
import './index.scss'

const sections = [
  ['我们处理的信息', '当你主动选择图片时，小程序会处理该图片以生成拼豆图纸；草稿、图纸参数与编辑记录用于保存和继续制作。'],
  ['权限使用', '相册读取仅在你选择图片时触发；保存到相册仅在你主动导出时触发。拒绝授权不会影响浏览设置和隐私说明。'],
  ['保存与清理', '本地草稿可在“设置—清理本地数据”中删除。你也可以在作品页删除对应作品。已保存到系统相册的图片请在系统相册中管理。'],
  ['信息共享', '我们不会出售你的个人信息，也不会将你选择的图片用于广告画像。为完成图片处理，数据可能提交至本产品后端服务。'],
  ['AI 功能', '当前送审版本未开放 AI 图片生成，不会收集提示词或生成相关内容。'],
  ['联系我们', '如需行使查阅、更正或删除数据等权利，请通过小程序主体在微信公众平台公示的联系方式联系我们。'],
]

export default function PrivacyPage() {
  return <View className='page-shell privacy-page'>
    <Text className='privacy-title'>隐私与数据说明</Text>
    <Text className='updated'>更新日期：2026 年 8 月 11 日</Text>
    <Text className='intro'>我们坚持最少、必要、透明的原则处理信息。以下说明应与微信公众平台中实际配置并公示的《小程序隐私保护指引》保持一致。</Text>
    {sections.map(([title, body]) => <View className='card privacy-section' key={title}>
      <Text className='section-title'>{title}</Text><Text className='section-body'>{body}</Text>
    </View>)}
  </View>
}
