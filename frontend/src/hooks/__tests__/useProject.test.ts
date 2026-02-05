import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/server'
import { useProject } from '@/hooks/useProject'

describe('useProject', () => {
  it('loads project data', async () => {
    const { result } = renderHook(() => useProject('p1'))

    await act(async () => {
      await result.current.loadProject()
    })

    expect(result.current.project?.id).toBe('p1')
    expect(result.current.error).toBeNull()
  })

  it('handles errors', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/projects/:projectId', () => {
        return new HttpResponse(null, { status: 500 })
      })
    )

    const { result } = renderHook(() => useProject('p2'))

    await act(async () => {
      await result.current.loadProject()
    })

    expect(result.current.project).toBeNull()
    expect(result.current.error).toBeTruthy()
  })
})
