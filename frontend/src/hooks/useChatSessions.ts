import { useCallback, useEffect, useState } from 'react'
import { getChatHistoryAPI, listChatSessionsAPI } from '@/services/chat.service'
import type { ChatMessage, ChatSessionSummary } from '@/types/chat.types'

export function useChatSessions(projectId?: string) {
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([])
  const [threadId, setThreadId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)

  const loadHistory = useCallback(
    async (targetThreadId: string) => {
      if (!projectId) return
      setLoadingHistory(true)
      try {
        const history = await getChatHistoryAPI(projectId, targetThreadId)
        setMessages(history.messages || [])
      } catch (err) {
        console.error('Failed to load chat history:', err)
        setMessages([])
      } finally {
        setLoadingHistory(false)
      }
    },
    [projectId]
  )

  const loadSessions = useCallback(
    async (selectLatest: boolean) => {
      if (!projectId) return
      try {
        const list = await listChatSessionsAPI(projectId)
        setSessions(list)
        if (selectLatest) {
          if (list.length > 0) {
            const latest = list[0]
            setThreadId(latest.thread_id)
            await loadHistory(latest.thread_id)
          } else {
            setThreadId(null)
            setMessages([])
          }
        }
      } catch (err) {
        console.error('Failed to load chat sessions:', err)
      }
    },
    [projectId, loadHistory]
  )

  const selectSession = useCallback(
    async (targetThreadId: string) => {
      if (isStreaming) return
      setThreadId(targetThreadId)
      await loadHistory(targetThreadId)
    },
    [isStreaming, loadHistory]
  )

  const startNewChat = useCallback(() => {
    if (isStreaming) return
    setThreadId(null)
    setMessages([])
  }, [isStreaming])

  useEffect(() => {
    if (threadId) {
      loadSessions(false)
    }
  }, [threadId, loadSessions])

  return {
    sessions,
    threadId,
    messages,
    loadingHistory,
    isStreaming,
    setIsStreaming,
    setThreadId,
    setMessages,
    loadSessions,
    selectSession,
    startNewChat,
  }
}
