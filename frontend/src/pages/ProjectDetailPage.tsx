import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import {
  getProjectAPI,
  provisionProjectAPI,
  stopProjectAPI,
  deleteProjectAPI,
  updateProjectAPI,
} from '@/services/project.service'
import { getAgentRunsAPI } from '@/services/agent.service'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import type { Project } from '@/types/project.types'
import type { AgentRunDetail } from '@/types/agent.types'
import { AgentLogStream } from '@/components/agent/AgentLogStream'
import {
  PlayCircle,
  StopCircle,
  RotateCcw,
  CheckCircle,
  Clock,
  XCircle,
  ChevronRight,
  Sparkles,
  FileCode,
  MessageSquare,
  Pencil,
  Trash2,
  RefreshCw,
} from 'lucide-react'
import { startAgentRunAPI, stopAgentRunAPI, resumeAgentRunAPI, resetRefactorSessionAPI } from '@/services/agent.service'
import { reprovisionProjectAPI } from '@/services/project.service'

// 狀態顏色映射
const statusColors: Record<string, 'default' | 'secondary' | 'destructive' | 'success' | 'warning'> = {
  CREATED: 'secondary',
  PROVISIONING: 'warning',
  READY: 'success',
  RUNNING: 'default',
  STOPPED: 'secondary',
  FAILED: 'destructive',
}

// 假資料（之後會逐步替換為真實資料）
const mockData = {
  testCoverage: 87,
  codeQuality: 92,
  tasks: [
    { id: '1', name: 'Performance Optimization', status: 'completed' as const, files: 5, added: 120, removed: 85 },
    { id: '2', name: 'Error Handling Enhancement', status: 'in_progress' as const, files: 3, added: 65, removed: 40 },
    { id: '3', name: 'Test Coverage Improvement', status: 'pending' as const, files: 0, added: 0, removed: 0 },
  ],
  report: {
    files: 8,
    lines: 185,
    currentStatus: 'Optimization phase in progress',
    achievements: [
      { text: 'Performance optimization completed', status: 'completed' },
      { text: 'Error handling enhancement in progress', status: 'in_progress' },
      { text: 'Test coverage improvement pending', status: 'pending' },
    ],
    metrics: {
      performanceImprovement: 35,
      testCoverage: 87,
      targetCoverage: 90,
      codeQuality: 92,
    },
  },
}

// 計算運行時間
function calculateRuntime(startTime: string): string {
  const start = new Date(startTime).getTime()
  const now = Date.now()
  const diff = now - start

  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((diff % (1000 * 60)) / 1000)

  if (hours > 0) {
    return `${hours}h ${minutes}m ${seconds}s`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds}s`
  }
  return `${seconds}s`
}

// 格式化時間
function formatTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuth()
  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [executing, setExecuting] = useState(false)
  const [runs, setRuns] = useState<AgentRunDetail[]>([])
  const [currentRun, setCurrentRun] = useState<AgentRunDetail | null>(null)
  const [selectedTab, setSelectedTab] = useState<'spec' | 'report' | 'diff'>('report')
  const [totalRuntime, setTotalRuntime] = useState('0s')
  const [iterationRuntime, setIterationRuntime] = useState('0s')

  // 編輯相關狀態
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    repo_url: '',
    branch: '',
    spec: '',
  })

  // Agent 控制狀態
  const [isStarting, setIsStarting] = useState(false)
  const [isStopping, setIsStopping] = useState(false)
  const [isResuming, setIsResuming] = useState(false)
  const [isReprovisioning, setIsReprovisioning] = useState(false)
  const [isResettingSession, setIsResettingSession] = useState(false)

  useEffect(() => {
    if (id) {
      loadProject()
      loadRuns()
    }
  }, [id])

  // 定時更新運行時間
  useEffect(() => {
    const interval = setInterval(() => {
      if (project?.created_at) {
        setTotalRuntime(calculateRuntime(project.created_at))
      }
      if (currentRun?.created_at && currentRun.status === 'RUNNING') {
        setIterationRuntime(calculateRuntime(currentRun.created_at))
      }
    }, 1000)
    return () => clearInterval(interval)
  }, [project?.created_at, currentRun?.created_at, currentRun?.status])

  // 輪詢狀態更新
  useEffect(() => {
    if (currentRun?.status === 'RUNNING') {
      const interval = setInterval(loadRuns, 5000)
      return () => clearInterval(interval)
    }
  }, [currentRun?.status])

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

  const loadRuns = async () => {
    try {
      const data = await getAgentRunsAPI(id!)
      setRuns(data.runs)

      // 找到最新的 RUNNING run 或最後一個 run
      const runningRun = data.runs.find((r) => r.status === 'RUNNING')
      if (runningRun) {
        setCurrentRun(runningRun)
      } else if (data.runs.length > 0) {
        setCurrentRun(data.runs[0])
      }
    } catch (error) {
      console.error('載入 Agent Runs 失敗', error)
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
        title: project.title || '',
        description: project.description || '',
        repo_url: project.repo_url || '',
        branch: project.branch,
        spec: project.spec,
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

  // Agent 控制函數
  const handleStartAgent = async () => {
    setIsStarting(true)
    try {
      await startAgentRunAPI(id!)
      await loadRuns()
    } catch (error: any) {
      alert(error.response?.data?.detail || '啟動失敗')
    } finally {
      setIsStarting(false)
    }
  }

  const handleStopAgent = async () => {
    if (!currentRun) return
    if (!confirm('確定要停止重構嗎？')) return

    setIsStopping(true)
    try {
      await stopAgentRunAPI(id!, currentRun.id)
      // 立即更新狀態為 STOPPED，停止輪詢
      setCurrentRun({ ...currentRun, status: 'STOPPED' })
      // 延遲一下再重新載入，讓後端有時間完成停止
      setTimeout(async () => {
        await loadRuns()
        await loadProject()
      }, 2000)
    } catch (error: any) {
      alert(error.response?.data?.detail || '停止失敗')
    } finally {
      setIsStopping(false)
    }
  }

  const handleResumeAgent = async () => {
    if (!currentRun) return

    setIsResuming(true)
    try {
      await resumeAgentRunAPI(id!, currentRun.id)
      await loadRuns()
    } catch (error: any) {
      alert(error.response?.data?.detail || '繼續失敗')
    } finally {
      setIsResuming(false)
    }
  }

  const handleReprovision = async () => {
    if (!confirm('確定要重設專案嗎？這將刪除容器並重新建立。')) return

    setIsReprovisioning(true)
    try {
      await reprovisionProjectAPI(id!)
      setCurrentRun(null)
      await loadProject()
      await loadRuns()
    } catch (error: any) {
      alert(error.response?.data?.detail || '重設失敗')
    } finally {
      setIsReprovisioning(false)
    }
  }

  const handleResetSession = async () => {
    if (!confirm('確定要重新開始重構嗎？這將清除之前的對話歷史，Agent 會從頭開始。')) return

    setIsResettingSession(true)
    try {
      await resetRefactorSessionAPI(id!)
      await loadProject()
      alert('重構會話已重設，下次開始重構時會建立新的會話')
    } catch (error: any) {
      alert(error.response?.data?.detail || '重設會話失敗')
    } finally {
      setIsResettingSession(false)
    }
  }

  const isRunning = currentRun?.status === 'RUNNING'
  const canStart = project?.status === 'READY' && !isRunning
  const isDone = currentRun?.status === 'DONE'
  const isFailed = currentRun?.status === 'FAILED'
  const isStopped = currentRun?.status === 'STOPPED'
  const canResume = isStopped || isFailed

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-lg text-gray-300">載入中...</div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-lg text-gray-300">專案不存在</div>
      </div>
    )
  }

  const projectName = project.title || project.repo_url?.split('/').pop()?.replace('.git', '') || 'Sandbox'

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm">
            <Link to="/projects" className="flex items-center gap-2 text-gray-400 hover:text-gray-200">
              <div className="w-6 h-6 bg-orange-500 rounded flex items-center justify-center text-white text-xs font-bold">
                smo
              </div>
              <span>AI 舊程式碼智能重構系統</span>
            </Link>
            <ChevronRight className="w-4 h-4 text-gray-600" />
            <span className="text-gray-200">{projectName}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-400">{user?.username || user?.email}</span>
            <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center text-sm">
              {(user?.username || user?.email || 'U').charAt(0).toUpperCase()}
            </div>
          </div>
        </div>
      </header>

      {/* Project Title Bar */}
      <div className="bg-gray-900 border-b border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold">{project.title || projectName}</h1>
              <button
                onClick={handleEdit}
                className="p-1 rounded hover:bg-gray-700 text-gray-400 hover:text-gray-200 transition-colors"
                title="編輯專案"
              >
                <Pencil className="w-4 h-4" />
              </button>
            </div>
            <Badge
              variant={statusColors[project.status]}
              className="flex items-center gap-1.5"
            >
              <span className={`w-2 h-2 rounded-full ${
                project.status === 'RUNNING' || isRunning ? 'bg-orange-400 animate-pulse' :
                project.status === 'READY' ? 'bg-green-400' :
                project.status === 'FAILED' ? 'bg-red-400' :
                'bg-gray-400'
              }`} />
              {isRunning ? 'RUNNING' : project.status} {currentRun ? `- Iteration ${currentRun.iteration_index}` : ''}
            </Badge>
          </div>
          <div className="flex items-center gap-3">
            {/* Chat Button */}
            {project.status === 'READY' && (
              <Link to={`/projects/${id}/chat`}>
                <Button variant="outline">
                  <MessageSquare className="w-4 h-4 mr-2" />
                  聊天
                </Button>
              </Link>
            )}
            {/* Main Action Button */}
            {project.status === 'CREATED' && (
              <Button onClick={handleProvision} disabled={executing}>
                {executing ? 'Provisioning...' : 'Provision'}
              </Button>
            )}
            {project.status === 'READY' && !isRunning && (
              <Button
                onClick={canResume ? handleResumeAgent : handleStartAgent}
                disabled={isStarting || isResuming}
                className="bg-purple-600 hover:bg-purple-700"
              >
                <PlayCircle className="w-4 h-4 mr-2" />
                {isStarting || isResuming ? '啟動中...' : canResume ? '繼續重構' : '開始重構'}
              </Button>
            )}
            {isRunning && (
              <Button
                onClick={handleStopAgent}
                variant="destructive"
                disabled={isStopping}
              >
                <StopCircle className="w-4 h-4 mr-2" />
                {isStopping ? '停止中...' : '停止重構'}
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* 編輯模式 */}
      {isEditing && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-semibold mb-4">編輯專案</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-300">專案標題</label>
                <Input
                  value={editForm.title}
                  onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                  placeholder="選填，未填則使用 repo 名稱"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-300">專案描述</label>
                <Textarea
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  placeholder="選填"
                  rows={2}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-300">Repository URL</label>
                <Input
                  value={editForm.repo_url}
                  onChange={(e) => setEditForm({ ...editForm, repo_url: e.target.value })}
                  disabled={project.status !== 'CREATED'}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-300">Branch</label>
                <Input
                  value={editForm.branch}
                  onChange={(e) => setEditForm({ ...editForm, branch: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-300">Spec</label>
                <Textarea
                  value={editForm.spec}
                  onChange={(e) => setEditForm({ ...editForm, spec: e.target.value })}
                  rows={5}
                  placeholder="描述重構目標、規格和期望結果..."
                />
              </div>
            </div>
            <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-700">
              <div className="flex gap-2">
                {/* 重新開始重構 - 只在有進行中會話時顯示 */}
                {project.refactor_thread_id && (
                  <Button
                    variant="ghost"
                    onClick={handleResetSession}
                    disabled={executing || isResettingSession || isRunning}
                    className="text-blue-400 hover:text-blue-300 hover:bg-blue-900/20"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    {isResettingSession ? '重設中...' : '重新開始'}
                  </Button>
                )}
                {project.status === 'READY' && !isRunning && (
                  <Button
                    variant="ghost"
                    onClick={handleReprovision}
                    disabled={executing || isReprovisioning}
                    className="text-orange-400 hover:text-orange-300 hover:bg-orange-900/20"
                  >
                    <RotateCcw className="w-4 h-4 mr-2" />
                    {isReprovisioning ? '重設中...' : '重設專案'}
                  </Button>
                )}
                <Button
                  variant="ghost"
                  onClick={handleDelete}
                  disabled={executing}
                  className="text-red-400 hover:text-red-300 hover:bg-red-900/20"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  刪除專案
                </Button>
              </div>
              <div className="flex gap-3">
                <Button variant="outline" onClick={handleCancelEdit} disabled={executing}>
                  取消
                </Button>
                <Button onClick={handleSaveEdit} disabled={executing}>
                  {executing ? '儲存中...' : '儲存'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content - Three Column Layout */}
      <div className="flex flex-col lg:flex-row h-[calc(100vh-140px)]">
        {/* Left Panel - Project Overview */}
        <div className="lg:w-72 xl:w-80 flex-shrink-0 overflow-y-auto border-r border-gray-800 bg-gray-850">
          {/* Project Overview Section */}
          <div className="p-4 border-b border-gray-800">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Project Overview</h2>
            <div className="space-y-3">
              <div>
                <h3 className="font-medium text-gray-200">{project.title || projectName}</h3>
                {project.description && (
                  <p className="text-sm text-gray-400 mt-1">{project.description}</p>
                )}
              </div>
              {project.repo_url && (
                <div className="text-xs text-gray-500 break-all">
                  {project.repo_url}
                </div>
              )}
            </div>
          </div>

          {/* Spec Section */}
          <div className="p-4 border-b border-gray-800">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Spec</h2>
            <p className="text-sm text-gray-300 leading-relaxed">{project.spec}</p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 border-b border-gray-800">
            <div className="p-3 border-r border-b border-gray-800">
              <div className="flex items-center gap-2 text-purple-400 mb-1">
                <Sparkles className="w-4 h-4" />
              </div>
              <div className="text-2xl font-bold">#{currentRun?.iteration_index || runs.length || 0}</div>
              <div className="text-xs text-gray-400">當前迭代</div>
            </div>
            <div className="p-3 border-b border-gray-800">
              <div className="flex items-center gap-2 text-green-400 mb-1">
                <CheckCircle className="w-4 h-4" />
              </div>
              <div className="text-2xl font-bold">{runs.filter(r => r.status === 'DONE').length}</div>
              <div className="text-xs text-gray-400">已完成</div>
            </div>
            <div className="p-3 border-r border-gray-800">
              <div className="flex items-center gap-2 text-blue-400 mb-1">
                <FileCode className="w-4 h-4" />
              </div>
              <div className="text-2xl font-bold">{mockData.testCoverage}%</div>
              <div className="text-xs text-gray-400">平均覆蓋率</div>
            </div>
            <div className="p-3">
              <div className="flex items-center gap-2 text-yellow-400 mb-1">
                <Sparkles className="w-4 h-4" />
              </div>
              <div className="text-2xl font-bold">{mockData.codeQuality}%</div>
              <div className="text-xs text-gray-400">程式品質</div>
            </div>
          </div>

          {/* Iterations List */}
          <div className="p-4">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Iterations</h2>
            <div className="space-y-2">
              {runs.length > 0 ? runs.slice(0, 5).map((run) => (
                <div
                  key={run.id}
                  className={`p-3 rounded-lg ${
                    currentRun?.id === run.id
                      ? 'border-l-2 border-purple-500 bg-purple-900/20'
                      : 'border-l-2 border-transparent bg-gray-800/50 hover:bg-gray-800'
                  } cursor-pointer transition-colors`}
                  onClick={() => setCurrentRun(run)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {run.status === 'DONE' ? (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      ) : run.status === 'RUNNING' ? (
                        <Sparkles className="w-4 h-4 text-purple-400 animate-pulse" />
                      ) : run.status === 'FAILED' ? (
                        <XCircle className="w-4 h-4 text-red-400" />
                      ) : (
                        <Clock className="w-4 h-4 text-gray-400" />
                      )}
                      <span className="font-medium">Iteration {run.iteration_index}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between mt-1 text-xs text-gray-400">
                    <span>{run.phase === 'plan' ? 'Initial Refactor' : run.phase === 'test' ? 'Optimization & Testing' : run.phase}</span>
                    <span>{run.created_at ? calculateRuntime(run.created_at) : '—'}</span>
                  </div>
                </div>
              )) : (
                <div className="text-sm text-gray-500 text-center py-4">
                  尚無迭代記錄
                </div>
              )}
            </div>
          </div>

        </div>

        {/* Middle Panel - Iteration Info */}
        <div className="lg:w-72 xl:w-80 flex-shrink-0 overflow-y-auto border-r border-gray-800">
          {/* Iteration Info Header */}
          <div className="grid grid-cols-2 border-b border-gray-800">
            <div className="p-4 border-r border-gray-800">
              <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Iteration N</h2>
              <div className="text-3xl font-bold">{currentRun?.iteration_index || runs.length || '—'}</div>
            </div>
            <div className="p-4">
              <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Iteration Info</h2>
              <Badge
                variant={isRunning ? 'warning' : isDone ? 'success' : isFailed ? 'destructive' : 'secondary'}
                className="text-sm"
              >
                {currentRun?.status || 'N/A'}
              </Badge>
            </div>
          </div>

          {/* Iteration Details */}
          <div className="p-4 border-b border-gray-800">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Iteration Info</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Phase</span>
                <span className="text-orange-400">{currentRun?.phase === 'plan' ? 'Optimization & Testing' : currentRun?.phase || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Start Time</span>
                <span>{currentRun?.created_at ? formatTime(currentRun.created_at) : '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Runtime</span>
                <span className="text-green-400">{iterationRuntime}</span>
              </div>
            </div>
          </div>

          {/* Metrics */}
          <div className="p-4 border-b border-gray-800">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Metrics</h2>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    Test Coverage
                  </span>
                  <span>{mockData.testCoverage}%</span>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 rounded-full transition-all duration-500"
                    style={{ width: `${mockData.testCoverage}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-yellow-400" />
                    Code Quality
                  </span>
                  <span>{mockData.codeQuality}%</span>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-yellow-500 rounded-full transition-all duration-500"
                    style={{ width: `${mockData.codeQuality}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Tasks */}
          <div className="p-4 border-b border-gray-800">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Tasks ({mockData.tasks.length})
            </h2>
            <div className="space-y-2">
              {mockData.tasks.map((task) => (
                <div
                  key={task.id}
                  className="p-3 rounded-lg bg-gray-800/50"
                >
                  <div className="flex items-center gap-2 mb-2">
                    {task.status === 'completed' ? (
                      <CheckCircle className="w-4 h-4 text-green-400" />
                    ) : task.status === 'in_progress' ? (
                      <Sparkles className="w-4 h-4 text-purple-400 animate-pulse" />
                    ) : (
                      <Clock className="w-4 h-4 text-gray-400" />
                    )}
                    <span className="text-sm font-medium">{task.name}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    <FileCode className="w-3 h-3" />
                    <span>{task.files}</span>
                    <span className="text-green-400">+{task.added}</span>
                    <span className="text-red-400">-{task.removed}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Right Panel - Report and Logs */}
        <div className="flex-1 min-w-0 flex flex-col overflow-hidden">
          {/* Report Section */}
          <div className="flex-1 flex flex-col min-h-0 border-b border-gray-800">
            {/* Report Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-400" />
                <span className="font-medium">
                  Iteration {currentRun?.iteration_index || runs.length || '—'} - {currentRun?.phase === 'plan' ? 'Optimization & Testing' : currentRun?.phase || 'Report'}
                </span>
              </div>
              <div className="flex items-center gap-4 text-sm text-gray-400">
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {currentRun?.created_at ? formatTime(currentRun.created_at) : '—'}
                </span>
                <span className="flex items-center gap-1">
                  <FileCode className="w-4 h-4" />
                  {mockData.report.files} files
                </span>
                <span>&lt;&gt; {mockData.report.lines} lines</span>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-gray-800">
              {(['spec', 'report', 'diff'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setSelectedTab(tab)}
                  className={`px-4 py-2 text-sm font-medium transition-colors ${
                    selectedTab === tab
                      ? 'text-gray-100 border-b-2 border-purple-500'
                      : 'text-gray-400 hover:text-gray-200'
                  }`}
                >
                  {tab}.md
                </button>
              ))}
            </div>

            {/* Report Content */}
            <div className="flex-1 p-4 overflow-y-auto">
              <div className="prose prose-invert prose-sm max-w-none">
                <h1 className="text-lg font-semibold text-gray-100">
                  # Iteration {currentRun?.iteration_index || runs.length || '—'} - Report {isRunning && <span className="text-orange-400">(In Progress)</span>}
                </h1>
                
                <h2 className="text-base font-medium text-gray-200 mt-4">## Current Status</h2>
                <p className="text-gray-400">{mockData.report.currentStatus}</p>
                
                <h2 className="text-base font-medium text-gray-200 mt-4">## Achievements So Far</h2>
                <ul className="space-y-1">
                  {mockData.report.achievements.map((achievement, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-gray-300">
                      {achievement.status === 'completed' ? (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      ) : achievement.status === 'in_progress' ? (
                        <span className="text-orange-400">🔄</span>
                      ) : (
                        <span className="text-red-400">🚫</span>
                      )}
                      {achievement.text}
                    </li>
                  ))}
                </ul>
                
                <h2 className="text-base font-medium text-gray-200 mt-4">## Preliminary Metrics</h2>
                <ul className="space-y-1 text-gray-400">
                  <li>- Performance improvement: {mockData.report.metrics.performanceImprovement}%</li>
                  <li>- Test coverage: {mockData.report.metrics.testCoverage}% (target: {mockData.report.metrics.targetCoverage}%)</li>
                  <li>- Code quality: {mockData.report.metrics.codeQuality}%</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Live Logs Section */}
          <div className="h-72 flex flex-col">
            <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-800">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span className="font-medium text-sm">Live Logs</span>
              {isRunning && (
                <span className="flex items-center gap-1 text-xs text-green-400">
                  <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  Streaming
                </span>
              )}
            </div>
            <div className="flex-1 overflow-hidden">
              {currentRun ? (
                <AgentLogStream
                  projectId={id!}
                  runId={currentRun.id}
                  autoStart={isRunning}
                />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500 text-sm bg-gray-900">
                  啟動重構後將顯示即時日誌
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
