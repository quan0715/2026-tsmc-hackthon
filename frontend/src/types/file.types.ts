export interface FileTreeNode {
  name: string
  path: string
  type: 'file' | 'directory'
  children?: FileTreeNode[]
}

export interface FileTreeResponse {
  root: string
  tree: FileTreeNode[]
}

export interface FileContentResponse {
  path: string
  content: string
  size: number
}

export interface OpenFile {
  path: string
  name: string
  content: string
  isLoading?: boolean
}
