import { X, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { FileIcon } from './FileIcon'
import type { OpenFile } from '@/types/file.types'
import { EmptyState } from '@/components/ui/EmptyState'
import { memo } from 'react'

// 副檔名對應語言
function getLanguage(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase()
  const languageMap: Record<string, string> = {
    // JavaScript / TypeScript
    js: 'javascript',
    jsx: 'jsx',
    ts: 'typescript',
    tsx: 'tsx',
    mjs: 'javascript',
    cjs: 'javascript',
    // Python
    py: 'python',
    pyw: 'python',
    pyi: 'python',
    // Web
    html: 'html',
    htm: 'html',
    css: 'css',
    scss: 'scss',
    sass: 'sass',
    less: 'less',
    // Data
    json: 'json',
    yml: 'yaml',
    yaml: 'yaml',
    xml: 'xml',
    toml: 'toml',
    // Shell
    sh: 'bash',
    bash: 'bash',
    zsh: 'bash',
    fish: 'bash',
    // Other languages
    go: 'go',
    rs: 'rust',
    java: 'java',
    kt: 'kotlin',
    scala: 'scala',
    c: 'c',
    cpp: 'cpp',
    h: 'c',
    hpp: 'cpp',
    cs: 'csharp',
    rb: 'ruby',
    php: 'php',
    swift: 'swift',
    r: 'r',
    sql: 'sql',
    graphql: 'graphql',
    gql: 'graphql',
    vue: 'vue',
    svelte: 'svelte',
    // Config
    dockerfile: 'docker',
    makefile: 'makefile',
    env: 'bash',
    gitignore: 'gitignore',
  }
  
  // 特殊檔名處理
  const lowerName = filename.toLowerCase()
  if (lowerName === 'dockerfile' || lowerName.startsWith('dockerfile.')) {
    return 'docker'
  }
  if (lowerName === 'makefile') {
    return 'makefile'
  }
  
  return languageMap[ext || ''] || 'text'
}

interface FileViewerProps {
  files: OpenFile[]
  activeFilePath: string | null
  onTabSelect: (path: string) => void
  onTabClose: (path: string) => void
}

export const FileViewer = memo(function FileViewer({
  files,
  activeFilePath,
  onTabSelect,
  onTabClose,
}: FileViewerProps) {
  const activeFile = files.find(f => f.path === activeFilePath)

  if (files.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-background text-muted-foreground">
        <EmptyState title="No file open" description="Select a file from the explorer" />
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Tabs */}
      <div className="flex items-center bg-background border-b border-border overflow-x-auto">
        {files.map((file) => (
          <div
            key={file.path}
            className={`flex items-center gap-2 px-3 py-2 text-sm cursor-pointer border-r border-border min-w-0 ${
              file.path === activeFilePath
                ? 'bg-background text-white'
                : 'bg-background text-muted-foreground hover:bg-background'
            }`}
            onClick={() => onTabSelect(file.path)}
          >
            <FileIcon filename={file.name} className="w-4 h-4 flex-shrink-0" />
            <span className="truncate max-w-[120px]">{file.name}</span>
            {file.isLoading ? (
              <Loader2 className="w-3 h-3 animate-spin flex-shrink-0" />
            ) : (
              <button
                className="hover:bg-secondary rounded p-0.5 flex-shrink-0"
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
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        ) : activeFile ? (
          activeFile.name.endsWith('.md') ? (
            <div className="p-4 prose prose-invert prose-sm max-w-none">
              <ReactMarkdown>{activeFile.content}</ReactMarkdown>
            </div>
          ) : (
            <SyntaxHighlighter
              language={getLanguage(activeFile.name)}
              style={vscDarkPlus}
              showLineNumbers
              wrapLines
              customStyle={{
                margin: 0,
                padding: '1rem',
                background: 'transparent',
                fontSize: '0.875rem',
                minHeight: '100%',
              }}
              lineNumberStyle={{
                minWidth: '3em',
                paddingRight: '1em',
                color: '#6b7280',
                userSelect: 'none',
              }}
            >
              {activeFile.content}
            </SyntaxHighlighter>
          )
        ) : null}
      </div>
    </div>
  )
})
