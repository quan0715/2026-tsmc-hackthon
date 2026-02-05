import { useCallback, useState } from 'react'
import { getProjectAPI } from '@/services/project.service'
import type { Project } from '@/types/project.types'
import { apiErrorMessage } from '@/utils/apiError'

export function useProject(projectId?: string) {
  const [project, setProject] = useState<Project | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadProject = useCallback(async () => {
    if (!projectId) return
    try {
      const data = await getProjectAPI(projectId)
      setProject(data)
      setError(null)
    } catch (err: any) {
      setError(apiErrorMessage(err, 'Failed to load project'))
    }
  }, [projectId])

  return {
    project,
    setProject,
    error,
    setError,
    loadProject,
  }
}
