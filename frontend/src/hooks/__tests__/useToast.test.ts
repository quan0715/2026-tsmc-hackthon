import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useToast } from '@/hooks/useToast'

describe('useToast', () => {
  it('adds and removes toasts', () => {
    const { result } = renderHook(() => useToast())

    act(() => {
      result.current.success('ok')
    })

    expect(result.current.toasts).toHaveLength(1)

    const id = result.current.toasts[0].id
    act(() => {
      result.current.removeToast(id)
    })

    expect(result.current.toasts).toHaveLength(0)
  })

  it('onClose removes the toast', () => {
    const { result } = renderHook(() => useToast())

    act(() => {
      result.current.error('boom')
    })

    expect(result.current.toasts).toHaveLength(1)

    act(() => {
      result.current.toasts[0].onClose?.()
    })

    expect(result.current.toasts).toHaveLength(0)
  })

  it('loading toast has duration 0', () => {
    const { result } = renderHook(() => useToast())

    act(() => {
      result.current.loading('loading')
    })

    expect(result.current.toasts).toHaveLength(1)
    expect(result.current.toasts[0].type).toBe('loading')
    expect(result.current.toasts[0].duration).toBe(0)
  })
})

