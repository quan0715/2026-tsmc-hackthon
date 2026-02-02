import { useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  getProjectAPI,
  provisionProjectAPI,
  execCommandAPI,
  stopProjectAPI,
  deleteProjectAPI,
  updateProjectAPI,
} from '@/services/project.service'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import type { Project } from '@/types/project.types'
import { AgentRunPanel } from '@/components/agent/AgentRunPanel'
import { cn } from '@/lib/utils'

const statusColors: Record<string, 'default' | 'secondary' | 'destructive' | 'success' | 'warning'> = {
  CREATED: 'secondary',
  PROVISIONING: 'warning',
  READY: 'success',
  RUNNING: 'default',
  STOPPED: 'secondary',
  FAILED: 'destructive',
}

interface LogEntry {
  text: string
  isAgent: boolean
}

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [project, setProject] = useState<Project | null>(null)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [command, setCommand] = useState('')
  const [loading, setLoading] = useState(true)
  const [executing, setExecuting] = useState(false)
  const logsEndRef = useRef<HTMLDivElement>(null)

  // 編輯相關狀態
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState({
    repo_url: '',
    branch: '',
    init_prompt: '',
  })

  useEffect(() => {
    if (id) {
      loadProject()
    }
  }, [id])

  useEffect(() => {
    if (project?.container_id) {
      setupLogStream()
    }
  }, [project?.container_id])

  useEffect(() => {
    // 自動捲動到日誌底部
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const loadProject = async () => {
    try {
      const data = await getProjectAPI(id!)
      setProject(data)
    } catch (error) {
      console.error('載入專案失敗', error)
    } finally {
      setLoading(false)
    }
  }

  const setupLogStream = () => {
    // EventSource 不支援自訂 Header，這裡使用 query parameter 傳遞 token
    // 注意：這不是最佳實踐，生產環境應該使用其他方案
    const eventSource = new EventSource(
      `${import.meta.env.VITE_API_BASE_URL}/api/v1/projects/${id}/logs/stream?follow=true&tail=50`,
      // 由於 EventSource 不支援自訂 headers，我們需要在後端支援從 query 參數讀取 token
      // 或者使用 fetch + ReadableStream 的方式
    )

    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.line) {
          const isAgentLog = data.line.includes('[AGENT-CONTAINER]')
          setLogs((prev) => [
            ...prev,
            {
              text: data.line,
              isAgent: isAgentLog,
            },
          ])
        }
      } catch (error) {
        console.error('解析日誌失敗', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE 連接錯誤', error)
      eventSource.close()
    }

    return () => {
      eventSource.close()
    }
  }

  const handleProvision = async () => {
    try {
      setExecuting(true)
      await provisionProjectAPI(id!)
      await loadProject()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Provision 失敗')
    } finally {
      setExecuting(false)
    }
  }

  const handleExecCommand = async () => {
    if (!command.trim()) return

    try {
      setExecuting(true)
      const result = await execCommandAPI(id!, { command })
      const newLogs: LogEntry[] = [
        { text: `$ ${command}`, isAgent: false },
        result.stdout && { text: result.stdout, isAgent: false },
        result.stderr && { text: result.stderr, isAgent: false },
      ].filter((log): log is LogEntry => Boolean(log && log.text))
      setLogs((prev) => [...prev, ...newLogs])
      setCommand('')
    } catch (error: any) {
      alert(error.response?.data?.detail || '執行指令失敗')
    } finally {
      setExecuting(false)
    }
  }

  const handleStop = async () => {
    if (!confirm('確定要停止此專案嗎？')) return

    try {
      await stopProjectAPI(id!)
      await loadProject()
    } catch (error: any) {
      alert(error.response?.data?.detail || '停止專案失敗')
    }
  }

  const handleDelete = async () => {
    if (!confirm('確定要刪除此專案嗎？此操作無法復原！')) return

    try {
      await deleteProjectAPI(id!)
      window.location.href = '/projects'
    } catch (error: any) {
      alert(error.response?.data?.detail || '刪除專案失敗')
    }
  }

  const handleEdit = () => {
    if (project) {
      setEditForm({
        repo_url: project.repo_url,
        branch: project.branch,
        init_prompt: project.init_prompt,
      })
      setIsEditing(true)
    }
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
  }

  const handleSaveEdit = async () => {
    try {
      setExecuting(true)
      const updated = await updateProjectAPI(id!, editForm)
      setProject(updated)
      setIsEditing(false)
    } catch (error: any) {
      alert(error.response?.data?.detail || '更新專案失敗')
    } finally {
      setExecuting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">載入中...</div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">專案不存在</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <Link to="/projects">
            <Button variant="ghost" size="sm">
              ← 返回專案列表
            </Button>
          </Link>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto p-8">
        {/* 專案資訊 */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>
                  {project.repo_url.split('/').pop()?.replace('.git', '') || project.repo_url}
                </CardTitle>
                <p className="text-sm text-gray-600 mt-1">{project.repo_url}</p>
              </div>
              <Badge variant={statusColors[project.status]}>{project.status}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {!isEditing ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <strong className="text-sm">分支：</strong>
                    <span className="text-sm ml-2">{project.branch}</span>
                  </div>
                  <div>
                    <strong className="text-sm">容器 ID：</strong>
                    <span className="text-sm ml-2 font-mono">
                      {project.container_id || '尚未建立'}
                    </span>
                  </div>
                  <div className="md:col-span-2">
                    <strong className="text-sm">初始提示：</strong>
                    <p className="text-sm mt-1 text-gray-700">{project.init_prompt}</p>
                  </div>
                  {project.last_error && (
                    <div className="md:col-span-2">
                      <strong className="text-sm text-red-600">錯誤訊息：</strong>
                      <p className="text-sm mt-1 text-red-600 bg-red-50 p-2 rounded">
                        {project.last_error}
                      </p>
                    </div>
                  )}
                </div>

                {/* 操作按鈕 */}
                <div className="flex gap-2 flex-wrap">
                  {project.status === 'CREATED' && (
                    <Button onClick={handleProvision} disabled={executing}>
                      {executing ? 'Provisioning...' : 'Provision 專案'}
                    </Button>
                  )}
                  {project.status === 'READY' && (
                    <Button onClick={handleStop} variant="outline">
                      停止專案
                    </Button>
                  )}
                  <Button onClick={handleEdit} variant="outline" size="sm">
                    編輯專案
                  </Button>
                  <Button onClick={loadProject} variant="outline" size="sm">
                    重新整理
                  </Button>
                  <Button onClick={handleDelete} variant="destructive" size="sm">
                    刪除專案
                  </Button>
                </div>
              </>
            ) : (
              <>
                {/* 編輯表單 */}
                <div className="space-y-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Repository URL
                      {project.status !== 'CREATED' && (
                        <span className="text-xs text-gray-500 ml-2">
                          (已 Provision，無法修改)
                        </span>
                      )}
                    </label>
                    <Input
                      placeholder="https://github.com/user/repo.git"
                      value={editForm.repo_url}
                      onChange={(e) => setEditForm({ ...editForm, repo_url: e.target.value })}
                      disabled={project.status !== 'CREATED'}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">分支</label>
                    <Input
                      placeholder="main"
                      value={editForm.branch}
                      onChange={(e) => setEditForm({ ...editForm, branch: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">初始提示</label>
                    <Textarea
                      placeholder="描述你想要 AI 執行的重構任務..."
                      value={editForm.init_prompt}
                      onChange={(e) => setEditForm({ ...editForm, init_prompt: e.target.value })}
                      rows={5}
                    />
                  </div>
                </div>

                {/* 編輯操作按鈕 */}
                <div className="flex gap-2">
                  <Button onClick={handleSaveEdit} disabled={executing}>
                    {executing ? '儲存中...' : '儲存'}
                  </Button>
                  <Button onClick={handleCancelEdit} variant="outline" disabled={executing}>
                    取消
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* AI Agent 自動分析 */}
        {project.status === 'READY' && (
          <AgentRunPanel projectId={id!} projectStatus={project.status} />
        )}

        {/* 執行指令 */}
        {project.status === 'READY' && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>執行指令</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Input
                  placeholder="輸入指令..."
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !executing) {
                      handleExecCommand()
                    }
                  }}
                  disabled={executing}
                />
                <Button onClick={handleExecCommand} disabled={executing}>
                  執行
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 容器日誌 */}
        {project.container_id && (
          <Card>
            <CardHeader>
              <CardTitle>容器日誌</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-black text-green-400 p-4 rounded h-96 overflow-auto font-mono text-sm">
                {logs.length === 0 ? (
                  <div className="text-gray-500">等待日誌輸出...</div>
                ) : (
                  logs.map((log, index) => (
                    <div
                      key={index}
                      className={cn(
                        'whitespace-pre-wrap',
                        log.isAgent ? 'text-blue-400 font-semibold' : 'text-green-400'
                      )}
                    >
                      {log.text}
                    </div>
                  ))
                )}
                <div ref={logsEndRef} />
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
