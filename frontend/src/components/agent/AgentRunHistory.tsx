import { Badge } from '@/components/ui/badge'
import type { AgentRunDetail } from '@/types/agent.types'

interface AgentRunHistoryProps {
  runs: AgentRunDetail[]
  projectId: string
}

export function AgentRunHistory({ runs }: AgentRunHistoryProps) {
  if (runs.length === 0) return null

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium">歷史記錄</h4>
      <div className="space-y-1">
        {runs.slice(0, 5).map((run) => (
          <div
            key={run.id}
            className="flex items-center justify-between text-sm p-2 rounded hover:bg-muted"
          >
            <span>Run #{run.iteration_index}</span>
            <div className="flex items-center gap-2">
              <Badge
                variant={run.status === 'DONE' ? 'success' : run.status === 'FAILED' ? 'destructive' : 'default'}
                className="text-xs"
              >
                {run.status}
              </Badge>
              <span className="text-xs text-muted-foreground">
                {new Date(run.created_at).toLocaleString('zh-TW')}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
