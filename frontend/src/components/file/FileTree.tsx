import { useState, memo } from 'react'
import { ChevronRight, ChevronDown, Folder, FolderOpen } from 'lucide-react'
import { FileIcon } from './FileIcon'
import type { FileTreeNode } from '@/types/file.types'
import { EmptyState } from '@/components/ui/EmptyState'
import { ScrollArea } from '@/components/ui/scroll-area'

interface FileTreeProps {
  tree: FileTreeNode[]
  onFileSelect: (path: string, name: string) => void
  selectedPath?: string
}

export const FileTree = memo(function FileTree({ tree, onFileSelect, selectedPath }: FileTreeProps) {
  return (
    <ScrollArea className="h-full bg-background">
      <div className="p-2">
        {tree.length === 0 ? (
          <EmptyState title="No files" />
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
    </ScrollArea>
  )
})

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
        className={`flex items-center gap-1 py-0.5 px-1 rounded cursor-pointer text-sm hover:bg-secondary ${
          isSelected ? 'bg-secondary text-white' : 'text-secondary-foreground'
        }`}
        style={{ paddingLeft }}
        onClick={handleClick}
      >
        {isDirectory ? (
          <>
            {isExpanded ? (
              <ChevronDown className="w-3 h-3 text-muted-foreground flex-shrink-0" />
            ) : (
              <ChevronRight className="w-3 h-3 text-muted-foreground flex-shrink-0" />
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
