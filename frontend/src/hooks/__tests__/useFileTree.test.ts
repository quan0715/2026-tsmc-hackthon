import { describe, it, expect } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useFileTree } from '@/hooks/useFileTree'

describe('useFileTree', () => {
  it('loads file tree', async () => {
    const { result } = renderHook(() => useFileTree('p1', 'container-1'))

    await act(async () => {
      await result.current.loadFileTree()
    })

    expect(result.current.fileTree.length).toBeGreaterThan(0)
  })

  it('opens and loads file content', async () => {
    const { result } = renderHook(() => useFileTree('p1', 'container-1'))

    await act(async () => {
      await result.current.handleFileSelect('repo/main.py', 'main.py')
    })

    await waitFor(() => {
      expect(result.current.openFiles.length).toBe(1)
      expect(result.current.openFiles[0].isLoading).toBe(false)
      expect(result.current.openFiles[0].content).toContain('print')
    })
  })
})
