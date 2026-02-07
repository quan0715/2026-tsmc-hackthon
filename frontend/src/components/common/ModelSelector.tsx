import { useState, useEffect, useRef, useMemo } from 'react'
import { getAvailableModelsAPI } from '@/services/models.service'
import type { ModelInfo } from '@/types/model.types'
import { ChevronDown } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'

interface Props {
  value?: string
  onChange: (model: string) => void
  disabled?: boolean
}

export function ModelSelector({ value, onChange, disabled }: Props) {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false
    const loadModels = async () => {
      try {
        const data = await getAvailableModelsAPI()
        if (cancelled) return
        setModels(data)
        if (!value && data.length > 0) {
          onChange(data[0].id)
        }
      } catch (err) {
        console.error('載入模型清單失敗:', err)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    loadModels()
    return () => { cancelled = true }
  }, [])

  // Close on outside click
  useEffect(() => {
    if (!open) return
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  // Group models by provider
  const grouped = useMemo(() => {
    const groups: Record<string, ModelInfo[]> = {}
    for (const m of models) {
      const p = m.provider || 'Other'
      if (!groups[p]) groups[p] = []
      groups[p].push(m)
    }
    return groups
  }, [models])

  const selected = models.find((m) => m.id === value)
  const displayName = loading ? '...' : selected?.display_name || 'Select model'

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => !disabled && setOpen(!open)}
        disabled={disabled}
        className="flex items-center gap-1 px-2 py-0.5 text-xs text-muted-foreground hover:text-secondary-foreground rounded hover:bg-secondary/50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <span className="truncate max-w-[180px]">{displayName}</span>
        <ChevronDown className="w-3 h-3 flex-shrink-0" />
      </button>

      {open && (
        <ScrollArea className="absolute bottom-full left-0 mb-1 w-72 max-h-80 bg-secondary border border-border rounded-lg shadow-xl z-50">
          {Object.entries(grouped).map(([provider, providerModels]) => (
            <div key={provider}>
              <div className="px-3 py-1.5 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider sticky top-0 bg-secondary">
                {provider}
              </div>
              {providerModels.map((model) => (
                <button
                  key={model.id}
                  type="button"
                  onClick={() => {
                    onChange(model.id)
                    setOpen(false)
                  }}
                  className={`w-full text-left px-3 py-1.5 hover:bg-secondary/60 transition-colors ${
                    model.id === value ? 'bg-secondary/40' : ''
                  }`}
                >
                  <div className="text-xs font-medium text-secondary-foreground">{model.display_name}</div>
                  <div className="text-[10px] text-muted-foreground mt-0.5">{model.description}</div>
                </button>
              ))}
            </div>
          ))}
        </ScrollArea>
      )}
    </div>
  )
}
