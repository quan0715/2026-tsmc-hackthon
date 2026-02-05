import { useCallback, useEffect, useState } from 'react'
import { getAgentRunsAPI } from '@/services/agent.service'
import type { AgentRunDetail } from '@/types/agent.types'

export function useAgentRuns(projectId?: string) {
  const [runs, setRuns] = useState<AgentRunDetail[]>([])
  const [currentRun, setCurrentRun] = useState<AgentRunDetail | null>(null)
  const [runtime, setRuntime] = useState('--:--:--')

  const loadRuns = useCallback(async () => {
    if (!projectId) return
    try {
      const data = await getAgentRunsAPI(projectId)
      const runsList = data.runs || []
      setRuns(runsList)
      const running = runsList.find((r: AgentRunDetail) => r.status === 'RUNNING')
      const latest = runsList[0]
      setCurrentRun(running || latest || null)
    } catch (err) {
      console.error('Failed to load runs:', err)
    }
  }, [projectId])

  useEffect(() => {
    if (currentRun?.status === 'RUNNING') {
      const interval = setInterval(loadRuns, 5000)
      return () => clearInterval(interval)
    }
  }, [currentRun?.status, loadRuns])

  useEffect(() => {
    const interval = setInterval(() => {
      if (currentRun?.created_at && currentRun.status === 'RUNNING') {
        const start = new Date(currentRun.created_at).getTime()
        const now = Date.now()
        const diff = Math.floor((now - start) / 1000)
        const h = Math.floor(diff / 3600)
        const m = Math.floor((diff % 3600) / 60)
        const s = diff % 60
        setRuntime(
          `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
        )
      } else {
        setRuntime('--:--:--')
      }
    }, 1000)
    return () => clearInterval(interval)
  }, [currentRun?.created_at, currentRun?.status])

  return {
    runs,
    currentRun,
    setCurrentRun,
    runtime,
    loadRuns,
  }
}
