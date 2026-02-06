import { useEffect, useRef, useState } from 'react'
import { streamAgentLogsAPI } from '@/services/agent.service'
import type { AgentLogEvent } from '@/types/agent.types'

interface UseAgentRunStreamOptions {
  projectId: string
  runId: string | null
  runCreatedAt?: string | null
  isRunning: boolean
  onLogEvent?: (event: AgentLogEvent) => void
  onError?: (error: Error) => void
  onReconnect?: () => void
}

/**
 * 自動管理 Agent Run 日誌串流，支援重連機制
 */
export function useAgentRunStream({
  projectId,
  runId,
  runCreatedAt,
  isRunning,
  onLogEvent,
  onError,
  onReconnect,
}: UseAgentRunStreamOptions) {
  const [isStreaming, setIsStreaming] = useState(false)
  const [isReconnecting, setIsReconnecting] = useState(false)
  const cancelStreamRef = useRef<(() => void) | null>(null)
  const mountTimeRef = useRef(Date.now())
  const reconnectingRef = useRef(false)
  const notifiedRunIdRef = useRef<string | null>(null)

  // 當 runId 或 isRunning 改變時，自動管理串流
  useEffect(() => {
    // 如果不需要串流，清理並返回
    if (!isRunning || !runId || !projectId) {
      if (cancelStreamRef.current) {
        cancelStreamRef.current()
        cancelStreamRef.current = null
      }
      setIsStreaming(false)
      setIsReconnecting(false)
      return
    }

    // 避免重複連線
    if (cancelStreamRef.current) {
      return
    }

    const shouldNotifyReconnect = () => {
      if (!runId) return false
      if (notifiedRunIdRef.current === runId) return false
      if (!runCreatedAt) return false
      const startedAt = Date.parse(runCreatedAt)
      if (Number.isNaN(startedAt)) return false
      return startedAt < mountTimeRef.current
    }

    // 啟動串流
    const startStream = async () => {
      try {
        setIsStreaming(true)

        if (shouldNotifyReconnect()) {
          setIsReconnecting(true)
          reconnectingRef.current = true
          notifiedRunIdRef.current = runId
          onReconnect?.()
        }

        const cancel = await streamAgentLogsAPI(
          projectId,
          runId,
          (event) => {
            // 第一個事件到達時，清除重連狀態
            if (reconnectingRef.current) {
              reconnectingRef.current = false
              setIsReconnecting(false)
            }
            onLogEvent?.(event)
          },
          (error) => {
            console.error('Stream error:', error)
            setIsStreaming(false)
            setIsReconnecting(false)
            reconnectingRef.current = false
            onError?.(error)
          }
        )

        cancelStreamRef.current = cancel
      } catch (error) {
        console.error('Failed to start stream:', error)
        setIsStreaming(false)
        setIsReconnecting(false)
        reconnectingRef.current = false
        onError?.(error as Error)
      }
    }

    startStream()

    // 清理函數
    return () => {
      if (cancelStreamRef.current) {
        cancelStreamRef.current()
        cancelStreamRef.current = null
      }
      setIsStreaming(false)
      setIsReconnecting(false)
      reconnectingRef.current = false
    }
  }, [isRunning, runId, projectId, runCreatedAt]) // 只依賴必要的值

  return {
    isStreaming,
    isReconnecting,
  }
}
