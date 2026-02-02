import { api } from './api'
import type { AgentRun, AgentRunDetail, AgentRunListResponse } from '@/types/agent.types'

/**
 * 啟動 Agent Run
 */
export const startAgentRunAPI = async (projectId: string): Promise<AgentRun> => {
  const response = await api.post(`/api/v1/projects/${projectId}/agent/run`, {})
  return response.data
}

/**
 * 取得專案的所有 Agent Runs
 */
export const getAgentRunsAPI = async (projectId: string): Promise<AgentRunListResponse> => {
  const response = await api.get(`/api/v1/projects/${projectId}/agent/runs`)
  return response.data
}

/**
 * 取得單一 Agent Run 詳情
 */
export const getAgentRunDetailAPI = async (
  projectId: string,
  runId: string
): Promise<AgentRunDetail> => {
  const response = await api.get(`/api/v1/projects/${projectId}/agent/runs/${runId}`)
  return response.data
}

/**
 * 取得 plan.md 下載 URL
 */
export const downloadPlanMdAPI = (projectId: string, runId: string): string => {
  return `${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/${projectId}/agent/runs/${runId}/artifacts/plan.md`
}

/**
 * 取得 plan.json 下載 URL
 */
export const downloadPlanJsonAPI = (projectId: string, runId: string): string => {
  return `${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/${projectId}/agent/runs/${runId}/artifacts/plan.json`
}
