export enum ProjectType {
  REFACTOR = 'REFACTOR',
  SANDBOX = 'SANDBOX',
}

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
  title?: string
  description?: string
  project_type: ProjectType
  repo_url?: string
  branch: string
  spec: string  // 重構規格說明（原 init_prompt）
  refactor_thread_id?: string  // 重構會話 ID
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
  title?: string
  description?: string
  project_type: ProjectType
  repo_url?: string
  branch: string
  spec: string  // 重構規格說明
}

export interface UpdateProjectRequest {
  title?: string
  description?: string
  repo_url?: string
  branch?: string
  spec?: string  // 重構規格說明
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
