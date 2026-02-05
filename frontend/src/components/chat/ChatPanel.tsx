import {
  useState,
  useRef,
  useEffect,
  useCallback,
  type Dispatch,
  type SetStateAction,
} from "react";
import {
  sendChatMessageAPI,
  streamChatResponseAPI,
  stopChatAPI,
} from "@/services/chat.service";
import type { ChatMessage, ChatStreamEvent } from "@/types/chat.types";
import type { Task } from "@/components/agent/TaskList";
import { Bot, User, Wrench, Square, Loader2, ArrowUp } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { EmptyState } from "@/components/ui/EmptyState";
import { apiErrorMessage } from "@/utils/apiError";

interface Props {
  projectId: string;
  threadId: string | null;
  messages: ChatMessage[];
  onThreadIdChange: Dispatch<SetStateAction<string | null>>;
  onMessagesChange: Dispatch<SetStateAction<ChatMessage[]>>;
  disabled?: boolean;
  onTasksUpdate?: (tasks: Task[]) => void;
  onStreamingChange?: (isStreaming: boolean) => void;
  loadingHistory?: boolean;
}

export function ChatPanel({
  projectId,
  threadId,
  messages,
  onThreadIdChange,
  onMessagesChange,
  disabled = false,
  onTasksUpdate,
  onStreamingChange,
  loadingHistory = false,
}: Props) {
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamHint, setStreamHint] = useState<string | null>(null);
  const [streamStart, setStreamStart] = useState<number | null>(null);
  const [elapsedText, setElapsedText] = useState<string>("0s");
  const [tokenUsage, setTokenUsage] = useState<{
    input_tokens?: number;
    output_tokens?: number;
    total_tokens?: number;
  } | null>(null);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const cancelStreamRef = useRef<(() => void) | null>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    onStreamingChange?.(isStreaming);
  }, [isStreaming, onStreamingChange]);

  useEffect(() => {
    if (!isStreaming) {
      setStreamHint(null);
      setStreamStart(null);
      setElapsedText("0s");
      setTokenUsage(null);
      return;
    }
    if (!streamHint) {
      const hints = [
        "Finagling...",
        "Reticulating splines...",
        "Tuning the prompt...",
        "Coaxing better answers...",
        "Herding tokens...",
        "Aligning context windows...",
        "Negotiating with entropy...",
        "Refactoring the thought chain...",
      ];
      const pick = hints[Math.floor(Math.random() * hints.length)];
      setStreamHint(pick);
    }
  }, [isStreaming, streamHint]);

  useEffect(() => {
    if (!isStreaming) return;
    if (!streamStart) {
      setStreamStart(Date.now());
      return;
    }
    const interval = setInterval(() => {
      const diff = Math.max(0, Math.floor((Date.now() - streamStart) / 1000));
      const m = Math.floor(diff / 60);
      const s = diff % 60;
      setElapsedText(m > 0 ? `${m}m ${s}s` : `${s}s`);
    }, 1000);
    return () => clearInterval(interval);
  }, [isStreaming, streamStart]);

  // Auto-resize textarea
  const adjustTextareaHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + "px";
    }
  }, []);

  useEffect(() => {
    adjustTextareaHeight();
  }, [input, adjustTextareaHeight]);

  const sendMessage = async () => {
    if (!input.trim() || isStreaming || disabled) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    onMessagesChange((prev) => [...prev, userMessage]);
    setInput("");
    setIsStreaming(true);
    setStreamStart(Date.now());
    setTokenUsage(null);

    const assistantMessageId = `assistant-${Date.now()}`;
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
    };
    onMessagesChange((prev) => [...prev, assistantMessage]);

    try {
      const response = await sendChatMessageAPI(
        projectId,
        userMessage.content,
        threadId || undefined
      );
      setCurrentTaskId(response.task_id);
      onThreadIdChange(response.thread_id);

      const cancelFn = await streamChatResponseAPI(
        projectId,
        response.task_id,
        (event: ChatStreamEvent) => {
          handleStreamEvent(event, assistantMessageId);
        },
        (error) => {
          console.error("Stream error:", error);
          setIsStreaming(false);
        }
      );
      cancelStreamRef.current = cancelFn;
    } catch (error: unknown) {
      console.error("Failed to send message:", error);
      const errorMessage = apiErrorMessage(error, "Failed to send");
      onMessagesChange((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: `Error: ${errorMessage}` }
            : msg
        )
      );
      setIsStreaming(false);
    }
  };

  const handleStreamEvent = (event: ChatStreamEvent, assistantMessageId: string) => {
    switch (event.type) {
      case "text_delta":
        if (event.content && typeof event.content === "object" && "delta" in event.content) {
          const delta = (event.content as { delta?: string }).delta || "";
          onMessagesChange((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId ? { ...msg, content: msg.content + delta } : msg
            )
          );
        }
        break;

      case "ai_content":
        if (event.content && typeof event.content === "object" && "content" in event.content) {
          const content = (event.content as { content?: string }).content || "";
          onMessagesChange((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId ? { ...msg, content: msg.content + content } : msg
            )
          );
        }
        break;

      case "tool_call_start":
        if (event.content) {
          const toolMessage: ChatMessage = {
            id: `tool-${Date.now()}`,
            role: "tool",
            content: "",
            timestamp: new Date().toISOString(),
            toolName: (event.content as { name?: string }).name,
            toolInput: event.content as Record<string, unknown>,
          };
          onMessagesChange((prev) => [...prev, toolMessage]);
        }
        break;

      case "tool_calls":
        if (event.content && "tool_calls" in event.content) {
          const toolCalls = (
            event.content as {
              tool_calls: Array<{ name: string; id: string; args: Record<string, unknown> }>;
            }
          ).tool_calls;
          const toolMessages: ChatMessage[] = toolCalls.map((tool) => ({
            id: `tool-${Date.now()}-${tool.id}`,
            role: "tool" as const,
            content: "",
            timestamp: new Date().toISOString(),
            toolName: tool.name,
            toolCallId: tool.id,
            toolInput: tool.args,
          }));
          onMessagesChange((prev) => [...prev, ...toolMessages]);
        }
        break;

      case "tool_call_result":
        if (event.content) {
          onMessagesChange((prev) => {
            const lastToolIdx = prev.findLastIndex((m) => m.role === "tool");
            if (lastToolIdx >= 0) {
              const newMessages = [...prev];
              newMessages[lastToolIdx] = {
                ...newMessages[lastToolIdx],
                toolOutput: JSON.stringify(event.content, null, 2),
              };
              return newMessages;
            }
            return prev;
          });
        }
        break;

      case "tools_execution":
        if (event.content && "results" in event.content) {
          const results = (
            event.content as {
              results: Array<{ name: string; tool_call_id: string; content: string }>;
            }
          ).results;
          onMessagesChange((prev) => {
            const newMessages = [...prev];
            for (const result of results) {
              const toolIdx = newMessages.findIndex(
                (m) =>
                  m.role === "tool" &&
                  (m.toolCallId === result.tool_call_id ||
                    (m.toolName === result.name && !m.toolOutput))
              );
              if (toolIdx >= 0) {
                newMessages[toolIdx] = {
                  ...newMessages[toolIdx],
                  toolOutput: result.content,
                };
              }
            }
            return newMessages;
          });

          // Handle task updates from write_todos
          for (const result of results) {
            if (result.name === "write_todos" && result.content) {
              const match = result.content.match(/Updated todo list to (\[.*\])/);
              if (match && match[1]) {
                try {
                  const jsonStr = match[1]
                    .replace(/'/g, '"')
                    .replace(/True/g, "true")
                    .replace(/False/g, "false")
                    .replace(/None/g, "null");
                  const tasks = JSON.parse(jsonStr);
                  onTasksUpdate?.(tasks);
                } catch (e) {
                  console.warn("Failed to parse write_todos result", e);
                }
              }
            }
          }
        }
        break;

      case "todo_update":
        if (event.content && "tasks" in event.content) {
          onTasksUpdate?.(event.content.tasks as Task[]);
        }
        break;

      case "status":
        if (event.content) {
          const status = (event.content as { status?: string }).status;
          if (status === "success" || status === "failed" || status === "stopped") {
            setIsStreaming(false);
            cancelStreamRef.current = null;
          }
        }
        break;

      case "token_usage":
        if (event.content && typeof event.content === "object") {
          setTokenUsage(event.content as {
            input_tokens?: number;
            output_tokens?: number;
            total_tokens?: number;
          });
        }
        break;

      case "log":
        if (event.message) {
          const match = event.message.match(/\[text_delta\]\s*(.+)/);
          if (match) {
            try {
              const data = JSON.parse(match[1]);
              if (data.delta) {
                onMessagesChange((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: msg.content + data.delta }
                      : msg
                  )
                );
              }
            } catch {
              // Ignore parse errors
            }
          }
        }
        break;

      case "error":
        setIsStreaming(false);
        break;
    }
  };

  const stopChat = async () => {
    if (cancelStreamRef.current) {
      cancelStreamRef.current();
      cancelStreamRef.current = null;
    }
    if (currentTaskId) {
      try {
        await stopChatAPI(projectId, currentTaskId);
      } catch (error) {
        console.error("Failed to stop chat:", error);
      }
    }
    setIsStreaming(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {loadingHistory && (
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Loader2 className="w-3 h-3 animate-spin" />
            Loading history...
          </div>
        )}
        {!loadingHistory && messages.length === 0 ? (
          <EmptyState title="Start a conversation" icon={<Bot className="w-10 h-10" />} />
        ) : (
          messages.map((msg) => <MessageEntry key={msg.id} message={msg} isStreaming={isStreaming} />)
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-2">
        <div className="flex items-end gap-2 bg-gray-800 rounded-xl border border-gray-700 focus-within:border-gray-600 transition-colors">
          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? "Project not ready..." : "Message..."}
            disabled={isStreaming || disabled}
            className="flex-1 bg-transparent px-3 py-2.5 text-sm text-gray-100 placeholder-gray-500 resize-none focus:outline-none min-h-[24px] max-h-[200px] leading-relaxed"
            rows={1}
          />

          {/* Send/Stop Button */}
          {isStreaming ? (
            <button
              onClick={stopChat}
              className="flex-shrink-0 w-8 h-8 mr-1.5 mb-1.5 rounded-lg bg-gray-600 hover:bg-gray-500 text-white flex items-center justify-center transition-colors"
            >
              <Square className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={sendMessage}
              disabled={!input.trim() || disabled}
              className="flex-shrink-0 w-8 h-8 mr-1.5 mb-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 text-white disabled:text-gray-500 flex items-center justify-center transition-colors disabled:cursor-not-allowed"
            >
              <ArrowUp className="w-4 h-4" />
            </button>
          )}
        </div>
        {isStreaming && streamHint && (
          <div className="px-2 pt-2 text-[11px] text-gray-500">
            {streamHint} ({elapsedText} · {formatTokens(tokenUsage)} tokens)
          </div>
        )}
      </div>
    </div>
  );
}

function formatTokens(
  usage: { input_tokens?: number; output_tokens?: number; total_tokens?: number } | null
) {
  if (!usage) return "--";
  const total =
    usage.total_tokens ??
    (usage.input_tokens || 0) + (usage.output_tokens || 0);
  if (!total) return "--";
  if (total >= 1000) {
    return `${(total / 1000).toFixed(1)}k`;
  }
  return `${total}`;
}

function MessageEntry({ message, isStreaming }: { message: ChatMessage; isStreaming: boolean }) {
  const { role, content, toolName, toolInput, toolOutput } = message;

  // User message
  if (role === "user") {
    return (
      <div className="flex gap-2 justify-end">
        <div className="max-w-[80%] bg-purple-600 rounded-lg px-3 py-2">
          <p className="text-sm text-white whitespace-pre-wrap">{content}</p>
        </div>
        <User className="w-4 h-4 text-purple-400 mt-1 flex-shrink-0" />
      </div>
    );
  }

  // Tool message
  if (role === "tool") {
    const subagentType =
      toolInput && typeof toolInput === "object"
        ? (toolInput as { subagent_type?: string }).subagent_type
        : undefined;
    const subagentDescription =
      toolInput && typeof toolInput === "object"
        ? (toolInput as { description?: string }).description
        : undefined;
    const displayName = subagentType ? `Subagent: ${subagentType}` : toolName || "Tool";
    const displayMeta = subagentType && toolName ? `tool: ${toolName}` : undefined;
    const displayArgs =
      toolInput && typeof toolInput === "object"
        ? Object.fromEntries(
            Object.entries(toolInput).filter(
              ([key]) => key !== "subagent_type" && key !== "description"
            )
          )
        : toolInput;

    return (
      <div className="flex gap-2">
        <Wrench className="w-4 h-4 text-blue-400 mt-1 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="text-sm text-blue-400 font-mono">{displayName}</div>
          {displayMeta && <div className="text-[10px] text-gray-500">{displayMeta}</div>}
          {subagentDescription && (
            <div className="text-xs text-gray-500 mt-1">{subagentDescription}</div>
          )}
          {displayArgs && Object.keys(displayArgs).length > 0 && (
            <details className="mt-1">
              <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                Args
              </summary>
              <pre className="text-xs text-gray-400 mt-1 overflow-x-auto">
                {JSON.stringify(displayArgs, null, 2)}
              </pre>
            </details>
          )}
          {toolOutput ? (
            <pre className="text-xs text-gray-400 mt-1 whitespace-pre-wrap overflow-x-auto max-h-40 overflow-y-auto">
              {toolOutput}
            </pre>
          ) : (
            <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
              <Loader2 className="w-3 h-3 animate-spin" />
              Running...
            </div>
          )}
        </div>
      </div>
    );
  }

  // Assistant message
  return (
    <div className="flex gap-2">
      <Bot className="w-4 h-4 text-purple-400 mt-1 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        {content ? (
          <div className="text-sm text-gray-200 prose prose-invert prose-sm max-w-none">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        ) : (
          isStreaming && <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse" />
        )}
      </div>
    </div>
  );
}
