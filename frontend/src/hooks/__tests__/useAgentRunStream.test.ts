import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'

vi.mock('@/services/agent.service', () => {
  return {
    streamAgentLogsAPI: vi.fn(),
  }
})

import { streamAgentLogsAPI } from '@/services/agent.service'
import { useAgentRunStream } from '@/hooks/useAgentRunStream'
import type { AgentLogEvent } from '@/types/agent.types'

describe('useAgentRunStream', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('starts streaming when running', async () => {
    const cancel = vi.fn()
    const streamMock = vi.mocked(streamAgentLogsAPI)
    streamMock.mockResolvedValue(cancel)

    const { result, unmount } = renderHook(() =>
      useAgentRunStream({
        projectId: 'p1',
        runId: 'r1',
        runCreatedAt: new Date(Date.now() + 1000).toISOString(),
        isRunning: true,
      })
    )

    await waitFor(() => {
      expect(result.current.isStreaming).toBe(true)
    })
    expect(streamMock.mock.calls.length).toBeGreaterThanOrEqual(1)
    expect(streamMock.mock.calls.length).toBeLessThanOrEqual(2)
    unmount()
  })

  it('cleans up the stream when stopped', async () => {
    const cancel = vi.fn()
    const streamMock = vi.mocked(streamAgentLogsAPI)
    streamMock.mockResolvedValue(cancel)

    const { rerender, unmount } = renderHook(
      (props: { isRunning: boolean }) =>
        useAgentRunStream({
          projectId: 'p1',
          runId: 'r1',
          runCreatedAt: new Date(Date.now() + 1000).toISOString(),
          isRunning: props.isRunning,
        }),
      { initialProps: { isRunning: true } }
    )

    await waitFor(() => {
      expect(streamMock.mock.calls.length).toBeGreaterThanOrEqual(1)
    })

    const before = cancel.mock.calls.length
    rerender({ isRunning: false })

    await waitFor(() => {
      expect(cancel.mock.calls.length).toBeGreaterThan(before)
    })
    unmount()
  })

  it('notifies reconnect when the run started before mount, and clears after first event', async () => {
    let onMessage: ((event: AgentLogEvent) => void) | undefined
    const cancel = vi.fn()
    const streamMock = vi.mocked(streamAgentLogsAPI)
    streamMock.mockImplementation(async (_projectId, _runId, onLogEvent) => {
      onMessage = onLogEvent
      return cancel
    })

    const onReconnect = vi.fn()

    const { result, unmount } = renderHook(() =>
      useAgentRunStream({
        projectId: 'p1',
        runId: 'r1',
        runCreatedAt: new Date(Date.now() - 10_000).toISOString(),
        isRunning: true,
        onReconnect,
      })
    )

    await waitFor(() => {
      expect(streamMock.mock.calls.length).toBeGreaterThanOrEqual(1)
    })

    await waitFor(() => {
      expect(result.current.isReconnecting).toBe(true)
    })
    expect(onReconnect.mock.calls.length).toBeGreaterThanOrEqual(1)
    expect(onReconnect.mock.calls.length).toBeLessThanOrEqual(2)

    act(() => {
      onMessage?.({ type: 'log', content: { message: 'hi' } } as AgentLogEvent)
    })

    await waitFor(() => {
      expect(result.current.isReconnecting).toBe(false)
    })
    unmount()
  })

  it('does not notify reconnect for a newly started run', async () => {
    const cancel = vi.fn()
    const streamMock = vi.mocked(streamAgentLogsAPI)
    streamMock.mockResolvedValue(cancel)

    const onReconnect = vi.fn()

    const { result, unmount } = renderHook(() =>
      useAgentRunStream({
        projectId: 'p1',
        runId: 'r1',
        runCreatedAt: new Date(Date.now() + 10_000).toISOString(),
        isRunning: true,
        onReconnect,
      })
    )

    await waitFor(() => {
      expect(streamMock.mock.calls.length).toBeGreaterThanOrEqual(1)
    })

    expect(onReconnect).toHaveBeenCalledTimes(0)
    expect(result.current.isReconnecting).toBe(false)
    unmount()
  })
})
