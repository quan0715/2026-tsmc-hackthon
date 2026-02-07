import type { ChatSessionSummary } from '@/types/chat.types'
import { ScrollArea } from '@/components/ui/scroll-area'

interface ChatSessionListProps {
  sessions: ChatSessionSummary[]
  activeThreadId: string | null
  disabled?: boolean
  onSelect: (threadId: string) => void
  onNew: () => void
}

export function ChatSessionList({
  sessions,
  activeThreadId,
  disabled = false,
  onSelect,
  onNew,
}: ChatSessionListProps) {
  return (
    <div className="border-b border-border">
      <div className="flex items-center justify-between px-2 py-1">
        <span className="text-xs text-muted-foreground uppercase">Sessions</span>
        <button
          onClick={onNew}
          disabled={disabled}
          className="text-[10px] px-2 py-0.5 rounded bg-secondary text-muted-foreground hover:text-foreground disabled:opacity-50"
        >
          New
        </button>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {sessions.length === 0 ? (
            <div className="text-[10px] text-muted-foreground">No sessions</div>
          ) : (
            sessions.map((session) => (
              <button
                key={session.thread_id}
                onClick={() => onSelect(session.thread_id)}
                disabled={disabled}
                className={`w-full text-left px-2 py-1 rounded text-[10px] font-mono transition ${
                  activeThreadId === session.thread_id
                    ? 'bg-secondary text-foreground'
                    : 'text-muted-foreground hover:bg-secondary/50'
                } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <div className="truncate">{session.title || session.thread_id}</div>
                <div className="text-[9px] text-muted-foreground">
                  {new Date(session.last_message_at).toLocaleString()}
                </div>
              </button>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
