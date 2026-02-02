import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, Circle, Loader2 } from 'lucide-react'

export interface Task {
  content: string
  status: 'pending' | 'in_progress' | 'completed'
}

interface TaskListProps {
  tasks: Task[]
}

export function TaskList({ tasks }: TaskListProps) {
  if (!tasks || tasks.length === 0) {
    return null
  }

  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          📋 執行任務清單
          <Badge variant="outline" className="ml-2">
            {tasks.filter(t => t.status === 'completed').length} / {tasks.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {tasks.map((task, index) => (
            <TaskItem key={index} task={task} index={index} />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function TaskItem({ task }: { task: Task; index: number }) {
  const getStatusIcon = () => {
    switch (task.status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-green-600" />
      case 'in_progress':
        return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
      case 'pending':
        return <Circle className="w-5 h-5 text-gray-400" />
    }
  }

  const getStatusColor = () => {
    switch (task.status) {
      case 'completed':
        return 'bg-green-50 border-green-200'
      case 'in_progress':
        return 'bg-blue-50 border-blue-200'
      case 'pending':
        return 'bg-gray-50 border-gray-200'
    }
  }

  const getStatusText = () => {
    switch (task.status) {
      case 'completed':
        return '已完成'
      case 'in_progress':
        return '進行中'
      case 'pending':
        return '待執行'
    }
  }

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${getStatusColor()}`}>
      <div className="flex-shrink-0 mt-0.5">
        {getStatusIcon()}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className={`text-sm ${task.status === 'completed' ? 'line-through text-gray-500' : 'text-gray-900'}`}>
            {task.content}
          </p>
          <Badge
            variant={
              task.status === 'completed' ? 'success' :
              task.status === 'in_progress' ? 'default' :
              'secondary'
            }
            className="flex-shrink-0 text-xs"
          >
            {getStatusText()}
          </Badge>
        </div>
      </div>
    </div>
  )
}
