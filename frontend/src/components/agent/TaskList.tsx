import { CheckCircle2, Circle, Loader2, ListTodo } from 'lucide-react'

export interface Task {
  content: string
  status: 'pending' | 'in_progress' | 'completed'
}

interface TaskListProps {
  tasks: Task[]
  compact?: boolean
}

export function TaskList({ tasks, compact = false }: TaskListProps) {
  if (!tasks || tasks.length === 0) {
    return null
  }

  const completedCount = tasks.filter(t => t.status === 'completed').length
  const inProgressCount = tasks.filter(t => t.status === 'in_progress').length

  if (compact) {
    return (
      <div className="space-y-1">
        {tasks.map((task, index) => (
          <CompactTaskItem key={index} task={task} />
        ))}
      </div>
    )
  }

  return (
    <div className="bg-background border border-border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-secondary/50 border-b border-border">
        <div className="flex items-center gap-2 text-sm text-secondary-foreground">
          <ListTodo className="w-4 h-4" />
          <span>Tasks</span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          {inProgressCount > 0 && (
            <span className="text-brand-blue-400">{inProgressCount} running</span>
          )}
          <span className="text-muted-foreground">
            {completedCount}/{tasks.length}
          </span>
        </div>
      </div>

      {/* Task List */}
      <div className="divide-y divide-border">
        {tasks.map((task, index) => (
          <TaskItem key={index} task={task} />
        ))}
      </div>
    </div>
  )
}

function TaskItem({ task }: { task: Task }) {
  return (
    <div className={`flex items-start gap-2 px-3 py-2 ${
      task.status === 'in_progress' ? 'bg-brand-blue-900/10' : ''
    }`}>
      <div className="flex-shrink-0 mt-0.5">
        <StatusIcon status={task.status} />
      </div>
      <span className={`text-sm ${
        task.status === 'completed' 
          ? 'text-muted-foreground line-through' 
          : task.status === 'in_progress'
          ? 'text-secondary-foreground'
          : 'text-muted-foreground'
      }`}>
        {task.content}
      </span>
    </div>
  )
}

function CompactTaskItem({ task }: { task: Task }) {
  return (
    <div className="flex items-start gap-2">
      <StatusIcon status={task.status} size="sm" />
      <span className={`text-xs ${
        task.status === 'completed' 
          ? 'text-muted-foreground line-through' 
          : task.status === 'in_progress'
          ? 'text-secondary-foreground'
          : 'text-muted-foreground'
      }`}>
        {task.content}
      </span>
    </div>
  )
}

function StatusIcon({ status, size = 'md' }: { status: Task['status']; size?: 'sm' | 'md' }) {
  const sizeClass = size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'
  
  switch (status) {
    case 'completed':
      return <CheckCircle2 className={`${sizeClass} text-green-500`} />
    case 'in_progress':
      return <Loader2 className={`${sizeClass} text-brand-blue-400 animate-spin`} />
    case 'pending':
      return <Circle className={`${sizeClass} text-muted-foreground/60`} />
  }
}
