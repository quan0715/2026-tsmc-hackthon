import type { ChatSessionSummary } from '@/types/chat.types'

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
    <div className="border-b border-gray-800">
      <div className="flex items-center justify-between px-2 py-1">
        <span className="text-xs text-gray-500 uppercase">Sessions</span>
        <button
          onClick={onNew}
          disabled={disabled}
          className="text-[10px] px-2 py-0.5 rounded bg-gray-800 text-gray-400 hover:text-white disabled:opacity-50"
        >
          New
        </button>
      </div>
      <div className="p-2 space-y-1 max-h-48 overflow-y-auto">
        {sessions.length === 0 ? (
          <div className="text-[10px] text-gray-500">No sessions</div>
        ) : (
          sessions.map((session) => (
            <button
              key={session.thread_id}
              onClick={() => onSelect(session.thread_id)}
              disabled={disabled}
              className={`w-full text-left px-2 py-1 rounded text-[10px] font-mono transition ${
                activeThreadId === session.thread_id
                  ? 'bg-gray-800 text-gray-100'
                  : 'text-gray-400 hover:bg-gray-800/50'
              } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <div className="truncate">{session.title || session.thread_id}</div>
              <div className="text-[9px] text-gray-500">
                {new Date(session.last_message_at).toLocaleString()}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  )
}
