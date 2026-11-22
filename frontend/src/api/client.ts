import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 180000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export default apiClient

/**
 * 提取 API 请求错误信息，兼容 FastAPI 常见错误响应。
 */
export function getApiErrorMessage(error: unknown, fallback = '请求失败，请稍后重试。'): string {
  if (axios.isAxiosError(error)) {
    const responseData = error.response?.data as { detail?: unknown; message?: unknown } | undefined

    const detail = responseData?.detail

    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }

    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (typeof item === 'object' && item !== null && 'msg' in item) {
            return String(item.msg)
          }
          return ''
        })
        .filter(Boolean)

      if (messages.length > 0) {
        return messages.join('；')
      }
    }

    if (typeof responseData?.message === 'string' && responseData.message.trim()) {
      return responseData.message
    }

    if (error.code === 'ECONNABORTED') {
      return '请求超时，请稍后重试。'
    }

    if (!error.response) {
      return '无法连接后端服务，请检查服务是否正常运行。'
    }
  }

  return error instanceof Error && error.message ? error.message : fallback
}
