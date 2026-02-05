import { useCallback, useState } from 'react'
import { getFileTreeAPI, getFileContentAPI } from '@/services/file.service'
import type { FileTreeNode, OpenFile } from '@/types/file.types'

export function useFileTree(projectId?: string, containerId?: string) {
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([])
  const [openFiles, setOpenFiles] = useState<OpenFile[]>([])
  const [activeFilePath, setActiveFilePath] = useState<string | null>(null)
  const [loadingTree, setLoadingTree] = useState(false)

  const loadFileTree = useCallback(async () => {
    if (!projectId || !containerId) return
    setLoadingTree(true)
    try {
      const data = await getFileTreeAPI(projectId)
      setFileTree(data.tree)
    } catch (err) {
      console.error('Failed to load file tree:', err)
    } finally {
      setLoadingTree(false)
    }
  }, [projectId, containerId])

  const handleFileSelect = useCallback(
    async (path: string, name: string) => {
      if (!projectId) return
      const existing = openFiles.find((f) => f.path === path)
      if (existing) {
        setActiveFilePath(path)
        return
      }

      const newFile: OpenFile = { path, name, content: '', isLoading: true }
      setOpenFiles((prev) => [...prev, newFile])
      setActiveFilePath(path)

      try {
        const data = await getFileContentAPI(projectId, path)
        setOpenFiles((prev) =>
          prev.map((f) =>
            f.path === path ? { ...f, content: data.content, isLoading: false } : f
          )
        )
      } catch (err) {
        console.error('Failed to load file:', err)
        setOpenFiles((prev) =>
          prev.map((f) =>
            f.path === path ? { ...f, content: 'Failed to load file', isLoading: false } : f
          )
        )
      }
    },
    [projectId, openFiles]
  )

  const handleTabClose = useCallback(
    (path: string) => {
      setOpenFiles((prev) => prev.filter((f) => f.path !== path))
      if (activeFilePath === path) {
        const remaining = openFiles.filter((f) => f.path !== path)
        setActiveFilePath(remaining.length > 0 ? remaining[remaining.length - 1].path : null)
      }
    },
    [activeFilePath, openFiles]
  )

  return {
    fileTree,
    openFiles,
    activeFilePath,
    loadingTree,
    loadFileTree,
    handleFileSelect,
    handleTabClose,
    setActiveFilePath,
  }
}
