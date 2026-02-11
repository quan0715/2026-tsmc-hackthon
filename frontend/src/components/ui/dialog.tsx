import { Button } from '@/components/ui/button'

interface DialogProps {
  open: boolean
  title: string
  message: string
  onClose: () => void
  actionLabel?: string
}

export function Dialog({ open, title, message, onClose, actionLabel = 'OK' }: DialogProps) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative w-full max-w-sm bg-background border border-border rounded-lg p-4 shadow-xl">
        <div className="text-sm text-foreground mb-2">{title}</div>
        <div className="text-xs text-muted-foreground mb-4 whitespace-pre-wrap">{message}</div>
        <div className="flex justify-end">
          <Button size="sm" onClick={onClose}>
            {actionLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
