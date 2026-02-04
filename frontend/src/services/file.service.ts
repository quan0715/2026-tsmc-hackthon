import { api } from './api'
import type { FileTreeResponse, FileContentResponse } from '@/types/file.types'

export const getFileTreeAPI = async (projectId: string): Promise<FileTreeResponse> => {
  const response = await api.get(`/api/v1/projects/${projectId}/files`)
  return response.data
}

export const getFileContentAPI = async (projectId: string, filePath: string): Promise<FileContentResponse> => {
  const response = await api.get(`/api/v1/projects/${projectId}/files/${filePath}`)
  return response.data
}
