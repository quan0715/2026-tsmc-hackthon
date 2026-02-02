import { api } from './api'
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '@/types/auth.types'

export const registerAPI = async (data: RegisterRequest): Promise<User> => {
  const response = await api.post<User>('/api/v1/auth/register', data)
  return response.data
}

export const loginAPI = async (data: LoginRequest): Promise<TokenResponse> => {
  const response = await api.post<TokenResponse>('/api/v1/auth/login', data)
  return response.data
}

export const getMeAPI = async (): Promise<User> => {
  const response = await api.get<User>('/api/v1/auth/me')
  return response.data
}
