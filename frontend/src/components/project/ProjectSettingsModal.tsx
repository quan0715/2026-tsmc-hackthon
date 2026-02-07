import { useState, useEffect } from 'react'
import { X, Save, Trash2, RefreshCw, RotateCcw, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import type { Project } from '@/types/project.types'
import { ScrollArea } from '@/components/ui/scroll-area'

interface ProjectSettingsModalProps {
  project: Project
  isOpen: boolean
  onClose: () => void
  onSave: (data: { title?: string; description?: string; spec?: string }) => Promise<void>
  onDelete: () => Promise<void>
  onReprovision: () => Promise<void>
  onResetSession: () => Promise<void>
  onExport: () => Promise<void>
}

export function ProjectSettingsModal({
  project,
  isOpen,
  onClose,
  onSave,
  onDelete,
  onReprovision,
  onResetSession,
  onExport,
}: ProjectSettingsModalProps) {
  const [title, setTitle] = useState(project.title || '')
  const [description, setDescription] = useState(project.description || '')
  const [spec, setSpec] = useState(project.spec || '')
  const [isSaving, setIsSaving] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [activeTab, setActiveTab] = useState<'general' | 'danger'>('general')

  useEffect(() => {
    setTitle(project.title || '')
    setDescription(project.description || '')
    setSpec(project.spec || '')
  }, [project])

  if (!isOpen) return null

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await onSave({ title, description, spec })
      onClose()
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async () => {
    if (confirm('確定要刪除此專案嗎？此操作無法復原。')) {
      await onDelete()
    }
  }

  const handleReprovision = async () => {
    if (confirm('確定要重設專案嗎？這將刪除容器並重新 clone repository。')) {
      await onReprovision()
      onClose()
    }
  }

  const handleResetSession = async () => {
    if (confirm('確定要重置重構會話嗎？這將清除所有對話歷史。')) {
      await onResetSession()
      onClose()
    }
  }

  const handleExport = async () => {
    setIsExporting(true)
    try {
      await onExport()
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative bg-background border border-border rounded-lg w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h2 className="text-lg font-medium">專案設定</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border">
          <button
            className={`px-4 py-2 text-sm ${
              activeTab === 'general'
                ? 'text-white border-b-2 border-brand-blue-500'
                : 'text-muted-foreground hover:text-white'
            }`}
            onClick={() => setActiveTab('general')}
          >
            一般
          </button>
          <button
            className={`px-4 py-2 text-sm ${
              activeTab === 'danger'
                ? 'text-white border-b-2 border-brand-blue-500'
                : 'text-muted-foreground hover:text-white'
            }`}
            onClick={() => setActiveTab('danger')}
          >
            危險操作
          </button>
        </div>

        {/* Content */}
        <ScrollArea className="flex-1">
        <div className="p-4">
          {activeTab === 'general' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-muted-foreground mb-1">專案名稱</label>
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="專案名稱"
                />
              </div>
              <div>
                <label className="block text-sm text-muted-foreground mb-1">描述</label>
                <Input
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="專案描述"
                />
              </div>
              <div>
                <label className="block text-sm text-muted-foreground mb-1">Repository</label>
                <Input
                  value={project.repo_url || ''}
                  disabled
                  className="opacity-50"
                />
                <p className="text-xs text-muted-foreground mt-1">Repository URL 無法修改</p>
              </div>
              <div>
                <label className="block text-sm text-muted-foreground mb-1">Spec</label>
                <Textarea
                  value={spec}
                  onChange={(e) => setSpec(e.target.value)}
                  placeholder="重構規格說明..."
                  rows={6}
                />
              </div>

              <div className="p-4 bg-secondary border border-border rounded-lg">
                <h3 className="text-sm font-medium mb-2">匯出 Workspace</h3>
                <p className="text-xs text-muted-foreground mb-3">
                  下載整個 workspace 的內容為壓縮檔案 (tar.gz)
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleExport}
                  disabled={isExporting || !project.container_id}
                >
                  <Download className="w-4 h-4 mr-2" />
                  {isExporting ? '匯出中...' : '匯出 Workspace'}
                </Button>
              </div>
            </div>
          )}

          {activeTab === 'danger' && (
            <div className="space-y-4">
              <div className="p-4 bg-yellow-900/20 border border-yellow-700/50 rounded-lg">
                <h3 className="text-sm font-medium text-yellow-400 mb-2">重置重構會話</h3>
                <p className="text-xs text-muted-foreground mb-3">
                  清除所有對話歷史，下次重構將從頭開始。
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleResetSession}
                  disabled={!project.refactor_thread_id}
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  重置會話
                </Button>
              </div>

              <div className="p-4 bg-orange-900/20 border border-orange-700/50 rounded-lg">
                <h3 className="text-sm font-medium text-orange-400 mb-2">重設專案</h3>
                <p className="text-xs text-muted-foreground mb-3">
                  刪除容器並重新 provision，所有本地修改將遺失。
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleReprovision}
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  重設專案
                </Button>
              </div>

              <div className="p-4 bg-red-900/20 border border-red-700/50 rounded-lg">
                <h3 className="text-sm font-medium text-red-400 mb-2">刪除專案</h3>
                <p className="text-xs text-muted-foreground mb-3">
                  永久刪除此專案和所有相關資料，此操作無法復原。
                </p>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleDelete}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  刪除專案
                </Button>
              </div>
            </div>
          )}
        </div>
        </ScrollArea>

        {/* Footer */}
        {activeTab === 'general' && (
          <div className="flex justify-end gap-2 px-4 py-3 border-t border-border">
            <Button variant="ghost" onClick={onClose}>
              取消
            </Button>
            <Button onClick={handleSave} disabled={isSaving}>
              <Save className="w-4 h-4 mr-2" />
              {isSaving ? '儲存中...' : '儲存'}
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
