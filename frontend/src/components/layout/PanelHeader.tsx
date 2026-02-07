import type { ReactNode } from 'react'

interface PanelHeaderProps {
  title: string
  right?: ReactNode
}

export function PanelHeader({ title, right }: PanelHeaderProps) {
  return (
    <div className="flex items-center justify-between px-2 py-1 border-b border-border">
      <span className="text-xs text-muted-foreground uppercase">{title}</span>
      {right}
    </div>
  )
}
