import { useState } from 'react'
import { ChevronRight, ChevronDown, Folder, FolderOpen, File } from 'lucide-react'
import type { FileTreeNode } from '@/types/file.types'

interface FileTreeProps {
  tree: FileTreeNode[]
  onFileSelect: (path: string, name: string) => void
  selectedPath?: string
}

export function FileTree({ tree, onFileSelect, selectedPath }: FileTreeProps) {
  return (
    <div className="h-full overflow-y-auto p-2 bg-gray-900">
      {tree.length === 0 ? (
        <div className="text-gray-500 text-xs text-center py-4">
          No files
        </div>
      ) : (
        tree.map((node) => (
          <TreeNode
            key={node.path}
            node={node}
            depth={0}
            onFileSelect={onFileSelect}
            selectedPath={selectedPath}
          />
        ))
      )}
    </div>
  )
}

interface TreeNodeProps {
  node: FileTreeNode
  depth: number
  onFileSelect: (path: string, name: string) => void
  selectedPath?: string
}

function TreeNode({ node, depth, onFileSelect, selectedPath }: TreeNodeProps) {
  const [isExpanded, setIsExpanded] = useState(depth < 2)
  const isDirectory = node.type === 'directory'
  const isSelected = selectedPath === node.path

  const handleClick = () => {
    if (isDirectory) {
      setIsExpanded(!isExpanded)
    } else {
      onFileSelect(node.path, node.name)
    }
  }

  const paddingLeft = depth * 12 + 8

  return (
    <div>
      <div
        className={`flex items-center gap-1 py-0.5 px-1 rounded cursor-pointer text-sm hover:bg-gray-800 ${
          isSelected ? 'bg-gray-800 text-white' : 'text-gray-300'
        }`}
        style={{ paddingLeft }}
        onClick={handleClick}
      >
        {isDirectory ? (
          <>
            {isExpanded ? (
              <ChevronDown className="w-3 h-3 text-gray-500 flex-shrink-0" />
            ) : (
              <ChevronRight className="w-3 h-3 text-gray-500 flex-shrink-0" />
            )}
            {isExpanded ? (
              <FolderOpen className="w-4 h-4 text-yellow-500 flex-shrink-0" />
            ) : (
              <Folder className="w-4 h-4 text-yellow-500 flex-shrink-0" />
            )}
          </>
        ) : (
          <>
            <span className="w-3" />
            <FileIcon filename={node.name} />
          </>
        )}
        <span className="truncate ml-1">{node.name}</span>
      </div>
      
      {isDirectory && isExpanded && node.children && (
        <div>
          {node.children.map((child) => (
            <TreeNode
              key={child.path}
              node={child}
              depth={depth + 1}
              onFileSelect={onFileSelect}
              selectedPath={selectedPath}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function FileIcon({ filename }: { filename: string }) {
  const ext = filename.split('.').pop()?.toLowerCase()
  
  // 根據副檔名決定顏色
  let colorClass = 'text-gray-400'
  
  switch (ext) {
    case 'ts':
    case 'tsx':
      colorClass = 'text-blue-400'
      break
    case 'js':
    case 'jsx':
      colorClass = 'text-yellow-400'
      break
    case 'py':
      colorClass = 'text-green-400'
      break
    case 'go':
      colorClass = 'text-cyan-400'
      break
    case 'rs':
      colorClass = 'text-orange-400'
      break
    case 'java':
      colorClass = 'text-red-400'
      break
    case 'json':
      colorClass = 'text-yellow-300'
      break
    case 'md':
      colorClass = 'text-blue-300'
      break
    case 'css':
    case 'scss':
      colorClass = 'text-pink-400'
      break
    case 'html':
      colorClass = 'text-orange-300'
      break
  }
  
  return <File className={`w-4 h-4 ${colorClass} flex-shrink-0`} />
}
