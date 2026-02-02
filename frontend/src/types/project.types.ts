export enum ProjectStatus {
  CREATED = 'CREATED',
  PROVISIONING = 'PROVISIONING',
  READY = 'READY',
  RUNNING = 'RUNNING',
  STOPPED = 'STOPPED',
  FAILED = 'FAILED',
  DELETED = 'DELETED',
}

export interface Project {
  id: string
  repo_url: string
  branch: string
  init_prompt: string
  status: ProjectStatus
  container_id?: string
  owner_id: string
  owner_email?: string
  created_at: string
  updated_at: string
  last_error?: string
  docker_status?: DockerStatus
}

export interface DockerStatus {
  id: string
  status: string
  state?: string
  inconsistent?: boolean
}

export interface CreateProjectRequest {
  repo_url: string
  branch: string
  init_prompt: string
}

export interface UpdateProjectRequest {
  repo_url?: string
  branch?: string
  init_prompt?: string
}

export interface ExecCommandRequest {
  command: string
  workdir?: string
}

export interface ExecCommandResponse {
  exit_code: number
  stdout: string
  stderr: string
}
