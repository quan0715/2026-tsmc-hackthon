import { useState, useEffect, useRef } from 'react'
import { getAvailableModelsAPI } from '@/services/models.service'
import type { ModelInfo } from '@/types/model.types'
import { ChevronDown } from 'lucide-react'

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

  const selected = models.find((m) => m.id === value)
  const displayName = loading ? '...' : selected?.display_name || 'Select model'

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => !disabled && setOpen(!open)}
        disabled={disabled}
        className="flex items-center gap-1 px-2 py-0.5 text-xs text-gray-400 hover:text-gray-200 rounded hover:bg-gray-700/50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <span className="truncate max-w-[180px]">{displayName}</span>
        <ChevronDown className="w-3 h-3 flex-shrink-0" />
      </button>

      {open && (
        <div className="absolute bottom-full left-0 mb-1 w-72 max-h-80 overflow-y-auto bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50">
          {models.map((model) => (
            <button
              key={model.id}
              type="button"
              onClick={() => {
                onChange(model.id)
                setOpen(false)
              }}
              className={`w-full text-left px-3 py-2 hover:bg-gray-700/60 transition-colors ${
                model.id === value ? 'bg-gray-700/40' : ''
              }`}
            >
              <div className="text-xs font-medium text-gray-200">{model.display_name}</div>
              <div className="text-[10px] text-gray-500 mt-0.5">{model.description}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
