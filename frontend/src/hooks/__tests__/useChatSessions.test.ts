import { describe, it, expect } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useChatSessions } from '@/hooks/useChatSessions'

describe('useChatSessions', () => {
  it('loads sessions and history', async () => {
    const { result } = renderHook(() => useChatSessions('p1'))

    await act(async () => {
      await result.current.loadSessions(true)
    })

    await waitFor(() => {
      expect(result.current.threadId).toBe('thread-1')
      expect(result.current.messages.length).toBeGreaterThan(0)
    })
  })

  it('resets on new chat', async () => {
    const { result } = renderHook(() => useChatSessions('p1'))

    await act(async () => {
      await result.current.loadSessions(true)
    })

    act(() => {
      result.current.startNewChat()
    })

    expect(result.current.threadId).toBeNull()
    expect(result.current.messages.length).toBe(0)
  })
})
