import { useEffect, useState, useRef } from 'react'
import type { AgentRunDetail } from '@/types/agent.types'
import { useAgentRunStream } from '@/hooks/useAgentRunStream'
import { Loader2, AlertCircle, CheckCircle, Square, Play } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { TaskList, type Task } from './TaskList'
import { ScrollArea } from '@/components/ui/scroll-area'

interface Props {
  projectId: string
  currentRun: AgentRunDetail | null
  onTasksUpdate?: (tasks: Task[]) => void
  onReconnect?: () => void
}

interface LogEntry {
  timestamp: string
  type: string
  content: any
}

export function AgentRunPanel({ projectId, currentRun, onTasksUpdate, onReconnect }: Props) {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const logsEndRef = useRef<HTMLDivElement>(null)

  const isRunning = currentRun?.status === 'RUNNING'

  const { isStreaming, isReconnecting } = useAgentRunStream({
    projectId,
    runId: currentRun?.id || null,
    runCreatedAt: currentRun?.created_at || null,
    isRunning,
    onLogEvent: (event) => {
      const timestamp = event.timestamp || new Date().toISOString()

      // 處理 task_list 事件
      if (event.type === 'task_list' && event.content?.tasks) {
        const newTasks = event.content.tasks.map((t: any) => ({
          id: t.id || String(Math.random()),
          title: t.title || t.task || '未命名任務',
          status: t.status || 'pending',
        }))
        setTasks(newTasks)
        onTasksUpdate?.(newTasks)
      }

      // 記錄所有日誌
      setLogs((prev) => [...prev, { timestamp, type: event.type, content: event.content }])
    },
    onError: (error) => {
      console.error('Stream error:', error)
    },
    onReconnect,
  })

  // 自動滾動到底部
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  // 清空日誌當 run 改變時
  useEffect(() => {
    if (currentRun?.id) {
      setLogs([])
      setTasks([])
    }
  }, [currentRun?.id])

  if (!currentRun) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-muted-foreground px-4">
        <Play className="w-12 h-12 mb-4 opacity-50" />
        <p className="text-sm">尚未啟動 Agent Run</p>
        <p className="text-xs mt-2">點擊「開始重構」按鈕來啟動</p>
      </div>
    )
  }

  const statusConfig = {
    RUNNING: { icon: Loader2, color: 'text-brand-blue-400', spin: true, label: '執行中' },
    DONE: { icon: CheckCircle, color: 'text-green-400', spin: false, label: '完成' },
    FAILED: { icon: AlertCircle, color: 'text-red-400', spin: false, label: '失敗' },
    STOPPED: { icon: Square, color: 'text-muted-foreground', spin: false, label: '已停止' },
  }

  const status = statusConfig[currentRun.status] || statusConfig.STOPPED
  const StatusIcon = status.icon

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="flex-shrink-0 px-3 py-2 border-b border-border bg-secondary/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <StatusIcon className={`w-4 h-4 ${status.color} ${status.spin ? 'animate-spin' : ''}`} />
            <span className="text-sm font-medium">{status.label}</span>
            {isReconnecting && (
              <span className="text-xs text-brand-blue-400 animate-pulse">重新連線中...</span>
            )}
          </div>
          <div className="text-xs text-muted-foreground">
            Run #{currentRun.id.slice(0, 8)}
          </div>
        </div>
        {currentRun.error_message && (
          <div className="mt-2 text-xs text-red-400">
            錯誤: {currentRun.error_message}
          </div>
        )}
      </div>

      {/* Tasks */}
      {tasks.length > 0 && (
        <ScrollArea className="flex-shrink-0 border-b border-border max-h-48">
          <TaskList tasks={tasks} compact />
        </ScrollArea>
      )}

      {/* Logs */}
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-2 text-xs font-mono">
          {logs.length === 0 && isRunning && (
            <div className="text-center text-muted-foreground py-8">
              <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
              <p>等待日誌...</p>
            </div>
          )}

          {logs.map((log, index) => (
            <LogEntry key={index} log={log} />
          ))}

          <div ref={logsEndRef} />
        </div>
      </ScrollArea>

      {/* Footer */}
      {isStreaming && (
        <div className="flex-shrink-0 px-3 py-2 border-t border-border bg-secondary/30">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span>即時串流中</span>
          </div>
        </div>
      )}
    </div>
  )
}

function LogEntry({ log }: { log: LogEntry }) {
  const renderContent = () => {
    switch (log.type) {
      case 'ai_content':
        return (
          <div className="text-secondary-foreground prose prose-sm max-w-none">
            <ReactMarkdown>{log.content.text || ''}</ReactMarkdown>
          </div>
        )

      case 'tool_call':
      case 'tool_calls':
        return (
          <div className="text-blue-400">
            🔧 呼叫工具: {log.content.tool_name || log.content.name || '未知'}
            {log.content.args && (
              <pre className="ml-4 mt-1 text-muted-foreground text-xs overflow-x-auto">
                {JSON.stringify(log.content.args, null, 2)}
              </pre>
            )}
          </div>
        )

      case 'tool_result':
        return (
          <div className="text-green-400">
            ✓ 工具結果
            {log.content.output && (
              <pre className="ml-4 mt-1 text-muted-foreground text-xs overflow-x-auto max-h-32">
                {typeof log.content.output === 'string'
                  ? log.content.output
                  : JSON.stringify(log.content.output, null, 2)}
              </pre>
            )}
          </div>
        )

      case 'thinking':
        return (
          <div className="text-yellow-400 italic">
            💭 {log.content.text || '思考中...'}
          </div>
        )

      case 'token_usage':
        return (
          <div className="text-muted-foreground">
            📊 Token 使用: 輸入 {log.content.input_tokens || 0} / 輸出 {log.content.output_tokens || 0}
          </div>
        )

      case 'status':
        return (
          <div className="text-brand-blue-400">
            📌 狀態: {log.content.status || '未知'}
          </div>
        )

      case 'log':
        return (
          <div className="text-muted-foreground">
            {log.content.message || JSON.stringify(log.content)}
          </div>
        )

      default:
        return (
          <div className="text-muted-foreground">
            {JSON.stringify(log.content)}
          </div>
        )
    }
  }

  return (
    <div className="border-l-2 border-border pl-3 py-1">
      <div className="text-muted-foreground/60 text-xs mb-1">
        [{new Date(log.timestamp).toLocaleTimeString()}] {log.type}
      </div>
      {renderContent()}
    </div>
  )
}
