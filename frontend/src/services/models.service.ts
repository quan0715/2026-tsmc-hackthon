import { api } from './api'
import type { ModelInfo } from '@/types/model.types'

export const getAvailableModelsAPI = async (): Promise<ModelInfo[]> => {
  const response = await api.get('/api/v1/models')
  return response.data
}
