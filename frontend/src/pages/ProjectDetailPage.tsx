import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  getProjectAPI,
  updateProjectAPI,
  deleteProjectAPI,
  provisionProjectAPI,
  reprovisionProjectAPI,
} from '@/services/project.service'
import {
  getAgentRunsAPI,
  stopAgentRunAPI,
  resetRefactorSessionAPI,
} from '@/services/agent.service'
import { getFileTreeAPI, getFileContentAPI } from '@/services/file.service'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ChatPanel } from '@/components/chat/ChatPanel'
import { TaskList, type Task } from '@/components/agent/TaskList'
import { FileTree } from '@/components/file/FileTree'
import { FileViewer } from '@/components/file/FileViewer'
import { ProjectSettingsModal } from '@/components/project/ProjectSettingsModal'
import type { Project } from '@/types/project.types'
import { AgentRunStatus } from '@/types/agent.types'
import type { AgentRunDetail } from '@/types/agent.types'
import type { FileTreeNode, OpenFile } from '@/types/file.types'
import {
  Square,
  Settings,
  ArrowLeft,
  Loader2,
  RefreshCw,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  GripVertical,
} from 'lucide-react'
import { Group, Panel, Separator } from 'react-resizable-panels'

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  // Project state
  const [project, setProject] = useState<Project | null>(null)
  const [, setRuns] = useState<AgentRunDetail[]>([])
  const [currentRun, setCurrentRun] = useState<AgentRunDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // File state
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([])
  const [openFiles, setOpenFiles] = useState<OpenFile[]>([])
  const [activeFilePath, setActiveFilePath] = useState<string | null>(null)
  const [loadingTree, setLoadingTree] = useState(false)

  // Task state
  const [tasks, setTasks] = useState<Task[]>([])

  // UI state
  const [showSettings, setShowSettings] = useState(false)
  const [isStopping, setIsStopping] = useState(false)
  const [isProvisioning, setIsProvisioning] = useState(false)

  // Panel collapse state (only left and right panels can collapse)
  const [infoCollapsed, setInfoCollapsed] = useState(false)
  const [treeCollapsed, setTreeCollapsed] = useState(false)

  // Runtime calculation
  const [runtime, setRuntime] = useState('00:00:00')

  // Load project data
  const loadProject = useCallback(async () => {
    if (!id) return
    try {
      const data = await getProjectAPI(id)
      setProject(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load project')
    }
  }, [id])

  // Load agent runs
  const loadRuns = useCallback(async () => {
    if (!id) return
    try {
      const data = await getAgentRunsAPI(id)
      const runsList = data.runs || []
      setRuns(runsList)
      const running = runsList.find((r: AgentRunDetail) => r.status === 'RUNNING')
      const latest = runsList[0]
      setCurrentRun(running || latest || null)
    } catch (err) {
      console.error('Failed to load runs:', err)
    }
  }, [id])

  // Load file tree
  const loadFileTree = useCallback(async () => {
    if (!id || !project?.container_id) return
    setLoadingTree(true)
    try {
      const data = await getFileTreeAPI(id)
      setFileTree(data.tree)
    } catch (err) {
      console.error('Failed to load file tree:', err)
    } finally {
      setLoadingTree(false)
    }
  }, [id, project?.container_id])

  // Initial load
  useEffect(() => {
    const init = async () => {
      setLoading(true)
      await loadProject()
      await loadRuns()
      setLoading(false)
    }
    init()
  }, [loadProject, loadRuns])

  // Load file tree when project is ready
  useEffect(() => {
    if (project?.status === 'READY' || project?.status === 'RUNNING') {
      loadFileTree()
    }
  }, [project?.status, loadFileTree])

  // Poll runs when agent is running
  useEffect(() => {
    if (currentRun?.status === 'RUNNING') {
      const interval = setInterval(loadRuns, 5000)
      return () => clearInterval(interval)
    }
  }, [currentRun?.status, loadRuns])

  // Update runtime
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

  // File operations
  const handleFileSelect = async (path: string, name: string) => {
    // Check if already open
    const existing = openFiles.find((f) => f.path === path)
    if (existing) {
      setActiveFilePath(path)
      return
    }

    // Add loading placeholder
    const newFile: OpenFile = { path, name, content: '', isLoading: true }
    setOpenFiles((prev) => [...prev, newFile])
    setActiveFilePath(path)

    // Load content
    try {
      const data = await getFileContentAPI(id!, path)
      setOpenFiles((prev) =>
        prev.map((f) =>
          f.path === path ? { ...f, content: data.content, isLoading: false } : f
        )
      )
    } catch (err) {
      console.error('Failed to load file:', err)
      setOpenFiles((prev) =>
        prev.map((f) =>
          f.path === path ? { ...f, content: 'Failed to load file', isLoading: false } : f
        )
      )
    }
  }

  const handleTabClose = (path: string) => {
    setOpenFiles((prev) => prev.filter((f) => f.path !== path))
    if (activeFilePath === path) {
      const remaining = openFiles.filter((f) => f.path !== path)
      setActiveFilePath(remaining.length > 0 ? remaining[remaining.length - 1].path : null)
    }
  }

  // Agent operations
  const handleProvision = async () => {
    if (!id) return
    setIsProvisioning(true)
    try {
      await provisionProjectAPI(id)
      await loadProject()
      await loadFileTree()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Provision failed')
    } finally {
      setIsProvisioning(false)
    }
  }

  const handleStopAgent = async () => {
    if (!id || !currentRun) return
    if (!confirm('確定要停止重構嗎？')) return
    setIsStopping(true)
    try {
      await stopAgentRunAPI(id, currentRun.id)
      setCurrentRun({ ...currentRun, status: AgentRunStatus.STOPPED })
      setTimeout(async () => {
        await loadRuns()
        await loadProject()
      }, 2000)
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to stop')
    } finally {
      setIsStopping(false)
    }
  }

  // Settings operations
  const handleSaveSettings = async (data: { title?: string; description?: string; spec?: string }) => {
    if (!id) return
    await updateProjectAPI(id, data)
    await loadProject()
  }

  const handleDelete = async () => {
    if (!id) return
    await deleteProjectAPI(id)
    navigate('/projects')
  }

  const handleReprovision = async () => {
    if (!id) return
    await reprovisionProjectAPI(id)
    await loadProject()
    await loadFileTree()
  }

  const handleResetSession = async () => {
    if (!id) return
    await resetRefactorSessionAPI(id)
    await loadProject()
  }

  // Loading state
  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-900">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    )
  }

  // Error state
  if (error || !project) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="text-red-400 mb-4">{error || 'Project not found'}</div>
          <Link to="/projects" className="text-purple-400 hover:underline">
            Back to projects
          </Link>
        </div>
      </div>
    )
  }

  const projectName = project.title || project.repo_url?.split('/').pop()?.replace('.git', '') || 'Project'
  const isRunning = currentRun?.status === 'RUNNING'
  const needsProvision = project.status === 'CREATED' || project.status === 'FAILED'

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-gray-100">
      {/* Header Bar */}
      <header className="h-10 flex items-center justify-between px-3 border-b border-gray-700 bg-gray-800 flex-shrink-0">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setInfoCollapsed(!infoCollapsed)}
            className="p-1 hover:bg-gray-700 rounded"
            title={infoCollapsed ? 'Expand left panel' : 'Collapse left panel'}
          >
            {infoCollapsed ? (
              <PanelLeftOpen className="w-4 h-4" />
            ) : (
              <PanelLeftClose className="w-4 h-4" />
            )}
          </button>
          <Link to="/projects" className="text-gray-400 hover:text-white">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <h1 className="text-sm font-medium truncate" title={projectName}>
            {projectName}
          </h1>
          <StatusBadge status={project.status} />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSettings(true)}
            className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
          >
            <Settings className="w-4 h-4" />
          </button>
          <button
            onClick={() => setTreeCollapsed(!treeCollapsed)}
            className="p-1 hover:bg-gray-700 rounded"
            title={treeCollapsed ? 'Expand right panel' : 'Collapse right panel'}
          >
            {treeCollapsed ? (
              <PanelRightOpen className="w-4 h-4" />
            ) : (
              <PanelRightClose className="w-4 h-4" />
            )}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <Group orientation="horizontal" className="flex-1">
        {/* Panel 1: Project Info */}
        {!infoCollapsed && (
          <>
            <Panel id="info" defaultSize="15%" minSize="10%" maxSize="25%">
              <div className="h-full flex flex-col border-r border-gray-800">
                <div className="flex items-center justify-between px-2 py-1 border-b border-gray-800">
                  <span className="text-xs text-gray-500 uppercase">Info</span>
                </div>
                <div className="p-2 space-y-2 text-xs border-b border-gray-800">
                  <div className="flex justify-between text-gray-400">
                    <span>Iteration</span>
                    <span className="text-white">#{currentRun?.iteration_index || 0}</span>
                  </div>
                  <div className="flex justify-between text-gray-400">
                    <span>Runtime</span>
                    <span className="text-white font-mono">{runtime}</span>
                  </div>
                  {currentRun && (
                    <div className="flex justify-between text-gray-400">
                      <span>Phase</span>
                      <span className="text-white capitalize">{currentRun.phase}</span>
                    </div>
                  )}
                </div>

                {tasks.length > 0 && (
                  <div className="flex-1 overflow-y-auto p-2">
                    <TaskList tasks={tasks} compact />
                  </div>
                )}

                {tasks.length === 0 && <div className="flex-1" />}

                {(needsProvision || isRunning) && (
                  <div className="p-2 space-y-2 border-t border-gray-800">
                    {needsProvision ? (
                      <Button className="w-full" size="sm" onClick={handleProvision} disabled={isProvisioning}>
                        {isProvisioning ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <RefreshCw className="w-4 h-4 mr-1" />}
                        Provision
                      </Button>
                    ) : isRunning ? (
                      <Button className="w-full" size="sm" variant="destructive" onClick={handleStopAgent} disabled={isStopping}>
                        {isStopping ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Square className="w-4 h-4 mr-1" />}
                        Stop
                      </Button>
                    ) : null}
                  </div>
                )}
              </div>
            </Panel>
            <Separator className="w-1 bg-gray-700 hover:bg-purple-600 transition-colors flex items-center justify-center">
              <GripVertical className="w-3 h-3 text-gray-500" />
            </Separator>
          </>
        )}

        {/* Panel 2: Chat */}
        <Panel id="chat" defaultSize="25%" minSize="10%" maxSize="50%">
          <div className="h-full flex flex-col border-r border-gray-800">
            <div className="flex items-center justify-between px-2 py-1 border-b border-gray-800">
              <span className="text-xs text-gray-500 uppercase">Chat</span>
            </div>
            <div className="flex-1 overflow-hidden">
              <ChatPanel
                projectId={id!}
                disabled={project.status !== 'READY'}
                onTasksUpdate={setTasks}
              />
            </div>
          </div>
        </Panel>

        <Separator className="w-1 bg-gray-700 hover:bg-purple-600 transition-colors flex items-center justify-center">
          <GripVertical className="w-3 h-3 text-gray-500" />
        </Separator>

        {/* Panel 3: File Viewer (main area) */}
        <Panel id="viewer" defaultSize="40%" minSize="20%">
          <div className="h-full overflow-hidden">
            <FileViewer
              files={openFiles}
              activeFilePath={activeFilePath}
              onTabSelect={setActiveFilePath}
              onTabClose={handleTabClose}
            />
          </div>
        </Panel>

        <Separator className="w-1 bg-gray-700 hover:bg-purple-600 transition-colors flex items-center justify-center">
          <GripVertical className="w-3 h-3 text-gray-500" />
        </Separator>

        {/* Panel 4: File Tree */}
        {!treeCollapsed && (
          <Panel id="tree" defaultSize="20%" minSize="10%" maxSize="35%">
            <div className="h-full flex flex-col border-l border-gray-800">
              <div className="flex items-center justify-between px-2 py-1 border-b border-gray-800">
                <span className="text-xs text-gray-500 uppercase">Explorer</span>
              </div>
              <div className="flex-1 overflow-hidden">
                {loadingTree ? (
                  <div className="h-full flex items-center justify-center">
                    <Loader2 className="w-6 h-6 animate-spin text-gray-500" />
                  </div>
                ) : (
                  <FileTree
                    tree={fileTree}
                    onFileSelect={handleFileSelect}
                    selectedPath={activeFilePath || undefined}
                  />
                )}
              </div>
            </div>
          </Panel>
        )}
      </Group>

      {/* Settings Modal */}
      <ProjectSettingsModal
        project={project}
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        onSave={handleSaveSettings}
        onDelete={handleDelete}
        onReprovision={handleReprovision}
        onResetSession={handleResetSession}
      />
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'success' | 'warning'> = {
    CREATED: 'secondary',
    PROVISIONING: 'warning',
    READY: 'success',
    RUNNING: 'default',
    STOPPED: 'secondary',
    FAILED: 'destructive',
  }

  return (
    <Badge variant={variants[status] || 'secondary'} className="text-xs">
      {status}
    </Badge>
  )
}
