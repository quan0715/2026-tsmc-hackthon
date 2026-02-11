import { useEffect, useState } from 'react'
import { X, CheckCircle, AlertCircle, Info, Loader2 } from 'lucide-react'

export type ToastType = 'success' | 'error' | 'info' | 'loading'

export interface ToastProps {
  id: string
  type: ToastType
  message: string
  duration?: number
  onClose?: () => void
}

export function Toast({ type, message, duration = 3000, onClose }: ToastProps) {
  const [isVisible, setIsVisible] = useState(true)

  useEffect(() => {
    if (type !== 'loading' && duration > 0 && onClose) {
      const timer = setTimeout(() => {
        setIsVisible(false)
        setTimeout(() => onClose(), 300) // 等待動畫完成
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [duration, type, onClose])

  const handleClose = () => {
    setIsVisible(false)
    if (onClose) {
      setTimeout(() => onClose(), 300)
    }
  }

  const icons = {
    success: <CheckCircle className="w-5 h-5 text-green-400" />,
    error: <AlertCircle className="w-5 h-5 text-red-400" />,
    info: <Info className="w-5 h-5 text-blue-400" />,
    loading: <Loader2 className="w-5 h-5 text-brand-blue-400 animate-spin" />,
  }

  const bgColors = {
    success: 'bg-green-900/20 border-green-700',
    error: 'bg-red-900/20 border-red-700',
    info: 'bg-blue-900/20 border-blue-700',
    loading: 'bg-brand-blue-900/20 border-brand-blue-700',
  }

  return (
    <div
      className={`
        flex items-center gap-3 px-4 py-3 rounded-lg border backdrop-blur-sm
        transition-all duration-300 shadow-lg
        ${bgColors[type]}
        ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-2'}
      `}
    >
      {icons[type]}
      <span className="text-sm text-foreground flex-1">{message}</span>
      {type !== 'loading' && (
        <button
          onClick={handleClose}
          className="text-muted-foreground hover:text-foreground transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}

export function ToastContainer({ toasts }: { toasts: ToastProps[] }) {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      <div className="pointer-events-auto space-y-2">
        {toasts.map((toast) => (
          <Toast key={toast.id} {...toast} />
        ))}
      </div>
    </div>
  )
}
