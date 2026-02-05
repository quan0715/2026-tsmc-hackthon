import { api } from './api'
import { getToken } from '@/utils/token'
import type {
  SendChatMessageResponse,
  ChatTaskStatus,
  ChatStreamEvent,
  ChatSessionSummary,
  ChatHistoryResponse,
} from '@/types/chat.types'

/**
 * 發送聊天訊息
 */
export const sendChatMessageAPI = async (
  projectId: string,
  message: string,
  threadId?: string
): Promise<SendChatMessageResponse> => {
  const response = await api.post(`/api/v1/projects/${projectId}/chat`, {
    message,
    thread_id: threadId,
    verbose: true,
  })
  return response.data
}

/**
 * 取得聊天任務狀態
 */
export const getChatStatusAPI = async (
  projectId: string,
  taskId: string
): Promise<ChatTaskStatus> => {
  const response = await api.get(
    `/api/v1/projects/${projectId}/chat/${taskId}/status`
  )
  return response.data
}

/**
 * 停止聊天任務
 */
export const stopChatAPI = async (
  projectId: string,
  taskId: string
): Promise<void> => {
  await api.post(`/api/v1/projects/${projectId}/chat/${taskId}/stop`)
}

/**
 * 取得聊天會話列表
 */
export const listChatSessionsAPI = async (
  projectId: string
): Promise<ChatSessionSummary[]> => {
  const response = await api.get(`/api/v1/projects/${projectId}/chat/sessions`)
  return response.data.sessions
}

/**
 * 取得聊天歷史
 */
export const getChatHistoryAPI = async (
  projectId: string,
  threadId: string
): Promise<ChatHistoryResponse> => {
  const response = await api.get(
    `/api/v1/projects/${projectId}/chat/sessions/${threadId}/history`
  )
  return response.data
}

/**
 * 串流聊天回應（SSE）
 * 使用 fetch + ReadableStream 以支援 Bearer token
 *
 * @param projectId 專案 ID
 * @param taskId 聊天任務 ID
 * @param onMessage 收到事件時的回調函數
 * @param onError 錯誤處理回調函數
 * @returns 返回取消串流的函數
 */
export const streamChatResponseAPI = async (
  projectId: string,
  taskId: string,
  onMessage: (event: ChatStreamEvent) => void,
  onError?: (error: Error) => void
): Promise<() => void> => {
  const token = getToken()
  if (!token) {
    throw new Error('未登入')
  }

  const url = `${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/${projectId}/chat/${taskId}/stream`

  const abortController = new AbortController()

  fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    signal: abortController.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let currentEvent = 'message'
      let currentData = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')

        // 保留最後一行（可能不完整）
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmedLine = line.trim()

          // 跳過註釋
          if (trimmedLine.startsWith(':')) continue

          // 空行表示事件結束
          if (trimmedLine === '') {
            if (currentData) {
              try {
                const data = JSON.parse(currentData)
                onMessage({
                  type: currentEvent as ChatStreamEvent['type'],
                  content: data,
                  timestamp: data.timestamp,
                  message: data.message,
                })
              } catch (e) {
                console.warn('解析 SSE 資料失敗', e, currentData)
              }
              // 重置狀態
              currentEvent = 'message'
              currentData = ''
            }
            continue
          }

          // 解析 event: 行
          if (trimmedLine.startsWith('event:')) {
            currentEvent = trimmedLine.slice(6).trim()
          }
          // 解析 data: 行
          else if (trimmedLine.startsWith('data:')) {
            currentData = trimmedLine.slice(5).trim()
          }
        }
      }
    })
    .catch((error) => {
      if (error.name !== 'AbortError') {
        onError?.(error)
      }
    })

  // 返回取消函數
  return () => abortController.abort()
}
