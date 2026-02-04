import { X, Loader2 } from 'lucide-react'
import type { OpenFile } from '@/types/file.types'

interface FileViewerProps {
  files: OpenFile[]
  activeFilePath: string | null
  onTabSelect: (path: string) => void
  onTabClose: (path: string) => void
}

export function FileViewer({ files, activeFilePath, onTabSelect, onTabClose }: FileViewerProps) {
  const activeFile = files.find(f => f.path === activeFilePath)

  if (files.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-900 text-gray-500">
        <div className="text-center">
          <div className="text-sm">No file open</div>
          <div className="text-xs mt-1">Select a file from the explorer</div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Tabs */}
      <div className="flex items-center bg-gray-950 border-b border-gray-800 overflow-x-auto">
        {files.map((file) => (
          <div
            key={file.path}
            className={`flex items-center gap-2 px-3 py-2 text-sm cursor-pointer border-r border-gray-800 min-w-0 ${
              file.path === activeFilePath
                ? 'bg-gray-900 text-white'
                : 'bg-gray-950 text-gray-400 hover:bg-gray-900'
            }`}
            onClick={() => onTabSelect(file.path)}
          >
            <span className="truncate max-w-[120px]">{file.name}</span>
            {file.isLoading ? (
              <Loader2 className="w-3 h-3 animate-spin flex-shrink-0" />
            ) : (
              <button
                className="hover:bg-gray-700 rounded p-0.5 flex-shrink-0"
                onClick={(e) => {
                  e.stopPropagation()
                  onTabClose(file.path)
                }}
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {activeFile?.isLoading ? (
          <div className="h-full flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-gray-500" />
          </div>
        ) : activeFile ? (
          <pre className="p-4 text-sm font-mono text-gray-300 whitespace-pre overflow-x-auto">
            <code>{activeFile.content}</code>
          </pre>
        ) : null}
      </div>
    </div>
  )
}
