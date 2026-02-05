import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/server'
import { useAgentRuns } from '@/hooks/useAgentRuns'

describe('useAgentRuns', () => {
  it('picks running run when available', async () => {
    const { result } = renderHook(() => useAgentRuns('p1'))

    await act(async () => {
      await result.current.loadRuns()
    })

    expect(result.current.currentRun?.status).toBe('RUNNING')
  })

  it('falls back to latest run when no running run', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/projects/:projectId/agent/runs', () => {
        return HttpResponse.json({
          total: 2,
          runs: [
            {
              id: 'run-2',
              project_id: 'p1',
              iteration_index: 0,
              phase: 'plan',
              status: 'DONE',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
            {
              id: 'run-1',
              project_id: 'p1',
              iteration_index: 0,
              phase: 'plan',
              status: 'FAILED',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
        })
      })
    )

    const { result } = renderHook(() => useAgentRuns('p1'))

    await act(async () => {
      await result.current.loadRuns()
    })

    expect(result.current.currentRun?.id).toBe('run-2')
  })
})
