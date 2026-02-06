import { http, HttpResponse } from 'msw'

const API_BASE_URL = 'http://localhost:8000'

export const handlers = [
  http.get(`${API_BASE_URL}/api/v1/git/branches`, () => {
    return HttpResponse.json({
      repo_url: 'https://github.com/example/repo.git',
      branches: ['main', 'dev'],
      default_branch: 'main',
    })
  }),

  http.get(`${API_BASE_URL}/api/v1/projects/:projectId`, ({ params }) => {
    const { projectId } = params
    return HttpResponse.json({
      id: projectId,
      title: 'Test Project',
      description: '',
      project_type: 'REFACTOR',
      repo_url: 'https://example.com/repo.git',
      branch: 'main',
      spec: '',
      status: 'READY',
      container_id: 'container-123',
      owner_id: 'user-1',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
  }),

  http.get(`${API_BASE_URL}/api/v1/projects/:projectId/agent/runs`, () => {
    return HttpResponse.json({
      total: 2,
      runs: [
        {
          id: 'run-1',
          project_id: 'p1',
          iteration_index: 0,
          phase: 'plan',
          status: 'RUNNING',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: 'run-0',
          project_id: 'p1',
          iteration_index: 0,
          phase: 'plan',
          status: 'DONE',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
    })
  }),

  http.get(`${API_BASE_URL}/api/v1/projects/:projectId/files`, () => {
    return HttpResponse.json({
      tree: [
        {
          name: 'repo',
          path: 'repo',
          type: 'directory',
          children: [
            { name: 'main.py', path: 'repo/main.py', type: 'file' },
          ],
        },
      ],
    })
  }),

  http.get(`${API_BASE_URL}/api/v1/projects/:projectId/files/:path*`, ({ params }) => {
    const path = params.path as string
    return HttpResponse.json({
      path,
      content: 'print(\"hello\")',
    })
  }),

  http.get(`${API_BASE_URL}/api/v1/projects/:projectId/chat/sessions`, () => {
    return HttpResponse.json({
      total: 1,
      sessions: [
        {
          thread_id: 'thread-1',
          project_id: 'p1',
          title: 'First message',
          created_at: new Date().toISOString(),
          last_message_at: new Date().toISOString(),
        },
      ],
    })
  }),

  http.get(`${API_BASE_URL}/api/v1/projects/:projectId/chat/sessions/:threadId/history`, ({ params }) => {
    const { threadId } = params
    return HttpResponse.json({
      thread_id: threadId,
      messages: [
        {
          id: 'msg-1',
          role: 'user',
          content: 'hello',
          timestamp: new Date().toISOString(),
        },
      ],
    })
  }),
]
