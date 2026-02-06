import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { ModelSelector } from '@/components/common/ModelSelector'
import { Play, Loader2 } from 'lucide-react'

interface Props {
  onStart: (model?: string) => Promise<void>
  disabled?: boolean
}

export function StartRefactorDialog({ onStart, disabled }: Props) {
  const [open, setOpen] = useState(false)
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const handleStart = async () => {
    try {
      setLoading(true)
      await onStart(selectedModel || undefined)
      setOpen(false)
    } catch (error) {
      console.error('啟動重構失敗:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Button disabled={disabled} size="sm" className="w-full" onClick={() => setOpen(true)}>
        <Play className="w-4 h-4 mr-1" />
        開始重構
      </Button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/60" onClick={() => !loading && setOpen(false)} />
          <div className="relative w-full max-w-sm bg-gray-900 border border-gray-800 rounded-lg p-4 shadow-xl">
            <div className="text-sm font-medium text-gray-100 mb-1">開始 AI 重構</div>
            <div className="text-xs text-gray-400 mb-4">
              選擇要使用的 AI 模型來分析和重構您的程式碼
            </div>
            <div className="mb-4">
              <label className="text-xs font-medium text-gray-300 mb-1.5 block">選擇模型</label>
              <ModelSelector
                value={selectedModel}
                onChange={setSelectedModel}
                disabled={loading}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setOpen(false)}
                disabled={loading}
              >
                取消
              </Button>
              <Button size="sm" onClick={handleStart} disabled={loading || !selectedModel}>
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-1" />
                ) : (
                  <Play className="w-4 h-4 mr-1" />
                )}
                {loading ? '啟動中...' : '開始執行'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
