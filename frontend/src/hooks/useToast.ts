import { useState, useCallback } from 'react'
import type { ToastProps, ToastType } from '@/components/ui/toast'

let toastId = 0

export function useToast() {
  const [toasts, setToasts] = useState<ToastProps[]>([])

  const addToast = useCallback((type: ToastType, message: string, duration?: number) => {
    const id = `toast-${++toastId}`
    const newToast: ToastProps = {
      id,
      type,
      message,
      duration,
      onClose: () => {
        setToasts((prev) => prev.filter((t) => t.id !== id))
      },
    }
    setToasts((prev) => [...prev, newToast])
    return id
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const success = useCallback((message: string, duration?: number) => {
    return addToast('success', message, duration)
  }, [addToast])

  const error = useCallback((message: string, duration?: number) => {
    return addToast('error', message, duration)
  }, [addToast])

  const info = useCallback((message: string, duration?: number) => {
    return addToast('info', message, duration)
  }, [addToast])

  const loading = useCallback((message: string) => {
    return addToast('loading', message, 0) // 0 = 不自動關閉
  }, [addToast])

  return {
    toasts,
    success,
    error,
    info,
    loading,
    removeToast,
  }
}
