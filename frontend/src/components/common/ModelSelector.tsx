import { useState, useEffect } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { getAvailableModelsAPI } from '@/services/models.service'
import type { ModelInfo } from '@/types/model.types'

interface Props {
  value?: string
  onChange: (model: string) => void
  disabled?: boolean
  className?: string
}

export function ModelSelector({ value, onChange, disabled, className }: Props) {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [loading, setLoading] = useState(true)

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

  return (
    <Select value={value} onValueChange={onChange} disabled={disabled || loading}>
      <SelectTrigger className={className}>
        <SelectValue placeholder={loading ? '載入中...' : '選擇模型'} />
      </SelectTrigger>
      <SelectContent>
        {models.map((model) => (
          <SelectItem key={model.id} value={model.id}>
            <div className="flex flex-col items-start">
              <span className="font-medium">{model.display_name}</span>
              <span className="text-xs text-muted-foreground">{model.description}</span>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
