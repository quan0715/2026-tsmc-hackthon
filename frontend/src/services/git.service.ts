import { api } from './api'

export type GitBranchesResponse = {
  repo_url: string
  branches: string[]
  default_branch: string | null
}

export const getGitBranchesAPI = async (repoUrl: string): Promise<GitBranchesResponse> => {
  const response = await api.get('/api/v1/git/branches', {
    params: { repo_url: repoUrl },
  })
  return response.data
}

