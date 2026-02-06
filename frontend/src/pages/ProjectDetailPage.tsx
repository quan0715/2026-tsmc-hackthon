import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { updateProjectAPI, deleteProjectAPI, provisionProjectAPI, reprovisionProjectAPI } from '@/services/project.service'
import { resetRefactorSessionAPI } from '@/services/agent.service'
import { Button } from '@/components/ui/button'
import { Dialog } from '@/components/ui/dialog'
import { ErrorState } from '@/components/ui/ErrorState'
import { ChatPanel } from '@/components/chat/ChatPanel'
import { TaskList, type Task } from '@/components/agent/TaskList'
import { FileTree } from '@/components/file/FileTree'
import { FileViewer } from '@/components/file/FileViewer'
import { ProjectSettingsModal } from '@/components/project/ProjectSettingsModal'
import { ToastContainer } from '@/components/ui/toast'
import { ProjectStatusBadge } from '@/components/project/ProjectStatusBadge'
import { ChatSessionList } from '@/components/chat/ChatSessionList'
import { PanelHeader } from '@/components/layout/PanelHeader'
import { apiErrorMessage } from '@/utils/apiError'
import { useProject } from '@/hooks/useProject'
import { useAgentRuns } from '@/hooks/useAgentRuns'
import { useFileTree } from '@/hooks/useFileTree'
import { useChatSessions } from '@/hooks/useChatSessions'
import { useToast } from '@/hooks/useToast'
import {
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
import { Panel, Group, Separator } from 'react-resizable-panels'

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)

  const { project, error, loadProject } = useProject(id)
  const { currentRun, runtime, loadRuns } = useAgentRuns(id)
  const {
    fileTree,
    openFiles,
    activeFilePath,
    loadingTree,
    loadFileTree,
    handleFileSelect,
    handleTabClose,
    setActiveFilePath,
  } = useFileTree(id, project?.container_id)
  const {
    sessions: chatSessions,
    threadId: chatThreadId,
    messages: chatMessages,
    loadingHistory: chatLoadingHistory,
    isStreaming: chatStreaming,
    setIsStreaming: setChatStreaming,
    setThreadId: setChatThreadId,
    setMessages: setChatMessages,
    loadSessions: loadChatSessions,
    selectSession: selectChatSession,
    startNewChat,
  } = useChatSessions(id)

  // Toast notifications
  const toast = useToast()

  // Task state
  const [tasks, setTasks] = useState<Task[]>([])

  // UI state
  const [showSettings, setShowSettings] = useState(false)
  const [isProvisioning, setIsProvisioning] = useState(false)
  const [dialog, setDialog] = useState<{ title: string; message: string } | null>(null)

  // Panel collapse state (only left and right panels can collapse)
  const [infoCollapsed, setInfoCollapsed] = useState(false)
  const [treeCollapsed, setTreeCollapsed] = useState(false)

  // 處理 Agent Run 重連（使用 useCallback 避免重複渲染）
  const handleAgentReconnect = useCallback(() => {
    toast.info('偵測到執行中的任務，正在重新連線...')
  }, [toast.info])

  // Initial load
  useEffect(() => {
    const init = async () => {
      setLoading(true)
      await loadProject()
      await loadRuns()
      await loadChatSessions(true)
      setLoading(false)
    }
    init()
  }, [loadProject, loadRuns, loadChatSessions])

  // Load file tree when project is ready
  useEffect(() => {
    if (project?.status === 'READY' || project?.status === 'RUNNING') {
      loadFileTree()
    }
  }, [project?.status, loadFileTree])

  // Agent operations
  const handleProvision = async () => {
    if (!id) return
    setIsProvisioning(true)
    try {
      await provisionProjectAPI(id)
      await loadProject()
      await loadFileTree()
    } catch (err: unknown) {
      setDialog({ title: 'Provision failed', message: apiErrorMessage(err, 'Provision failed') })
    } finally {
      setIsProvisioning(false)
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
      <ErrorState
        title="Project not found"
        message={error || 'Unable to load project'}
        actionLabel="Back to projects"
        onAction={() => navigate('/projects')}
      />
    )
  }

  const projectName = project.title || project.repo_url?.split('/').pop()?.replace('.git', '') || 'Project'
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
          <ProjectStatusBadge status={project.status} />
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
                <PanelHeader title="Info" />
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

                <ChatSessionList
                  sessions={chatSessions}
                  activeThreadId={chatThreadId}
                  disabled={chatStreaming}
                  onSelect={selectChatSession}
                  onNew={startNewChat}
                />

                {tasks.length > 0 && (
                  <div className="flex-1 overflow-y-auto p-2">
                    <TaskList tasks={tasks} compact />
                  </div>
                )}

                {tasks.length === 0 && <div className="flex-1" />}

                {needsProvision && (
                  <div className="p-2 space-y-2 border-t border-gray-800">
                    <Button className="w-full" size="sm" onClick={handleProvision} disabled={isProvisioning}>
                      {isProvisioning ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <RefreshCw className="w-4 h-4 mr-1" />}
                      Provision
                    </Button>
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
            <PanelHeader title="Chat" />
            <div className="flex-1 overflow-hidden">
              <ChatPanel
                projectId={id!}
                threadId={chatThreadId}
                messages={chatMessages}
                onThreadIdChange={setChatThreadId}
                onMessagesChange={setChatMessages}
                onStreamingChange={setChatStreaming}
                loadingHistory={chatLoadingHistory}
                disabled={project.status !== 'READY'}
                onTasksUpdate={setTasks}
                currentRun={currentRun}
                onReconnect={handleAgentReconnect}
              />
            </div>
          </div>
        </Panel>

        <Separator className="w-px bg-gray-800 hover:bg-gray-700 transition-colors flex items-center justify-center">
          <GripVertical className="w-2 h-2 text-gray-600 opacity-60" />
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

        <Separator className="w-px bg-gray-800 hover:bg-gray-700 transition-colors flex items-center justify-center">
          <GripVertical className="w-2 h-2 text-gray-600 opacity-60" />
        </Separator>

        {/* Panel 4: File Tree */}
        {!treeCollapsed && (
          <Panel id="tree" defaultSize="20%" minSize="10%" maxSize="35%">
            <div className="h-full flex flex-col border-l border-gray-800">
              <PanelHeader
                title="Explorer"
                right={(
                  <button
                    onClick={loadFileTree}
                    disabled={loadingTree}
                    className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white disabled:opacity-50"
                    title="Refresh"
                  >
                    <RefreshCw className={`w-3 h-3 ${loadingTree ? 'animate-spin' : ''}`} />
                  </button>
                )}
              />
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

      {/* Toast Container */}
      <ToastContainer toasts={toast.toasts} />

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
      <Dialog
        open={!!dialog}
        title={dialog?.title || ''}
        message={dialog?.message || ''}
        onClose={() => setDialog(null)}
      />
    </div>
  )
}
