import type { ReactNode } from 'react'

interface PanelHeaderProps {
  title: string
  right?: ReactNode
}

export function PanelHeader({ title, right }: PanelHeaderProps) {
  return (
    <div className="flex items-center justify-between px-2 py-1 border-b border-gray-800">
      <span className="text-xs text-gray-500 uppercase">{title}</span>
      {right}
    </div>
  )
}
