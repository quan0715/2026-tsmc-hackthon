/**
 * 聊天相關型別定義
 */

// 專案類型
export type ProjectType = 'REFACTOR' | 'SANDBOX'

// 聊天訊息角色
export type ChatRole = 'user' | 'assistant' | 'system' | 'tool'

// 聊天訊息
export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  timestamp: string
  // 工具呼叫相關
  toolName?: string
  toolCallId?: string
  toolInput?: Record<string, unknown>
  toolOutput?: string
  // Token 使用統計
  tokenUsage?: TokenUsage
}

// Token 使用統計
export interface TokenUsage {
  input_tokens: number
  output_tokens: number
  total_tokens: number
}

// 發送聊天訊息請求
export interface SendChatMessageRequest {
  message: string
  threadId?: string
  verbose?: boolean
}

// 發送聊天訊息回應
export interface SendChatMessageResponse {
  task_id: string
  thread_id: string
  project_id: string
  status: string
  message: string
}

// 聊天任務狀態
export interface ChatTaskStatus {
  task_id: string
  thread_id: string | null
  project_id: string
  status: 'RUNNING' | 'DONE' | 'FAILED' | 'STOPPED'
  created_at: string | null
  started_at: string | null
  finished_at: string | null
  error_message: string | null
}

// SSE 事件類型
export type ChatEventType =
  | 'log'
  | 'text_delta'
  | 'ai_content'        // ChunkParser 格式
  | 'tool_call_start'
  | 'tool_calls'        // ChunkParser 格式
  | 'tool_call_result'
  | 'tools_execution'   // ChunkParser 格式
  | 'token_usage'
  | 'todo_update'       // ChunkParser 格式
  | 'response_metadata' // ChunkParser 格式
  | 'status'
  | 'error'

// 聊天串流事件
export interface ChatStreamEvent {
  type: ChatEventType
  content?: Record<string, unknown>
  timestamp?: string
  message?: string
}

// 聊天會話
export interface ChatSession {
  threadId: string
  projectId: string
  messages: ChatMessage[]
  isStreaming: boolean
  createdAt: string
  lastMessageAt: string
}

// 聊天會話（列表用）
export interface ChatSessionSummary {
  thread_id: string
  project_id: string
  title?: string
  created_at: string
  last_message_at: string
}

// 聊天歷史回應
export interface ChatHistoryResponse {
  thread_id: string
  messages: ChatMessage[]
}
