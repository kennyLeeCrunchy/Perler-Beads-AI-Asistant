import { Button, Text, View } from '@tarojs/components'
import './index.scss'

interface Props {
  kind: 'loading' | 'error' | 'empty'
  title: string
  description?: string
  actionText?: string
  onAction?: () => void
}

export default function StatusPanel({ kind, title, description, actionText, onAction }: Props) {
  return <View className={`status-panel status-panel--${kind}`}>
    {kind === 'loading' && <View className='status-panel__spinner' />}
    <Text className='status-panel__title'>{title}</Text>
    {description && <Text className='status-panel__description'>{description}</Text>}
    {actionText && onAction && <Button className='status-panel__action' onClick={onAction}>{actionText}</Button>}
  </View>
}
