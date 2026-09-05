export function toUserMessage(reason: unknown): string {
  if (reason && typeof reason === 'object') {
    const err = reason as { errMsg?: string; message?: string }
    const message = err.message || err.errMsg || ''
    if (/cancel/i.test(message)) return ''
    if (/timeout/i.test(message)) return '处理超时，请检查网络后重试'
    if (/fail|network/i.test(message)) return '网络连接异常，请稍后重试'
    if (message) return message
  }
  return '暂时无法完成转换，请稍后重试'
}
