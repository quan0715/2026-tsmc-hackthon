import type { ReactNode } from 'react'

interface EmptyStateProps {
  title: string
  description?: string
  icon?: ReactNode
}

export function EmptyState({ title, description, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-muted-foreground text-sm">
      {icon && <div className="mb-3 opacity-50">{icon}</div>}
      <p className="text-sm">{title}</p>
      {description && <p className="text-xs mt-2 text-muted-foreground">{description}</p>}
    </div>
  )
}
