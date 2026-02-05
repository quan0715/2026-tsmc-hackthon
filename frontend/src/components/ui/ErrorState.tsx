import { Button } from '@/components/ui/button'

interface ErrorStateProps {
  title: string
  message?: string
  actionLabel?: string
  onAction?: () => void
}

export function ErrorState({ title, message, actionLabel, onAction }: ErrorStateProps) {
  return (
    <div className="h-screen flex items-center justify-center bg-gray-900">
      <div className="text-center">
        <div className="text-red-400 mb-3 text-sm">{title}</div>
        {message && <div className="text-gray-500 text-xs mb-4">{message}</div>}
        {actionLabel && onAction && (
          <Button size="sm" onClick={onAction}>
            {actionLabel}
          </Button>
        )}
      </div>
    </div>
  )
}
