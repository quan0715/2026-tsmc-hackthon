import { useState, useRef, useEffect } from "react";
import {
  sendChatMessageAPI,
  streamChatResponseAPI,
  stopChatAPI,
} from "@/services/chat.service";
import type { ChatMessage, ChatStreamEvent } from "@/types/chat.types";
import type { Task } from "@/components/agent/TaskList";
import { Bot, User, Wrench, Terminal, Send, Square, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface Props {
  projectId: string;
  disabled?: boolean;
  onTasksUpdate?: (tasks: Task[]) => void;
}

export function ChatPanel({ projectId, disabled = false, onTasksUpdate }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const cancelStreamRef = useRef<(() => void) | null>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isStreaming || disabled) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsStreaming(true);

    const assistantMessageId = `assistant-${Date.now()}`;
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, assistantMessage]);

    try {
      const response = await sendChatMessageAPI(
        projectId,
        userMessage.content,
        threadId || undefined
      );
      setCurrentTaskId(response.task_id);
      setThreadId(response.thread_id);

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
      const err = error as { response?: { data?: { detail?: string } } };
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: `Error: ${err.response?.data?.detail || "Failed to send"}` }
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
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId ? { ...msg, content: msg.content + delta } : msg
            )
          );
        }
        break;

      case "ai_content":
        if (event.content && typeof event.content === "object" && "content" in event.content) {
          const content = (event.content as { content?: string }).content || "";
          setMessages((prev) =>
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
          setMessages((prev) => [...prev, toolMessage]);
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
          setMessages((prev) => [...prev, ...toolMessages]);
        }
        break;

      case "tool_call_result":
        if (event.content) {
          setMessages((prev) => {
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
          setMessages((prev) => {
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

      case "log":
        if (event.message) {
          const match = event.message.match(/\[text_delta\]\s*(.+)/);
          if (match) {
            try {
              const data = JSON.parse(match[1]);
              if (data.delta) {
                setMessages((prev) =>
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
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 text-sm">
            <Bot className="w-10 h-10 mb-3 opacity-50" />
            <p>Start a conversation</p>
          </div>
        ) : (
          messages.map((msg) => <MessageEntry key={msg.id} message={msg} isStreaming={isStreaming} />)
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-800 p-2">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? "Project not ready..." : "Type a message..."}
            disabled={isStreaming || disabled}
            className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 placeholder-gray-500 resize-none focus:outline-none focus:border-purple-500 min-h-[40px] max-h-[120px]"
            rows={1}
          />
          {isStreaming ? (
            <button
              onClick={stopChat}
              className="px-3 bg-red-600 hover:bg-red-700 rounded text-white flex items-center justify-center"
            >
              <Square className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={sendMessage}
              disabled={!input.trim() || disabled}
              className="px-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded text-white flex items-center justify-center"
            >
              <Send className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
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
    return (
      <div className="flex gap-2">
        <Wrench className="w-4 h-4 text-blue-400 mt-1 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="text-sm text-blue-400 font-mono">{toolName}</div>
          {toolInput && Object.keys(toolInput).length > 0 && (
            <details className="mt-1">
              <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                Args
              </summary>
              <pre className="text-xs text-gray-400 mt-1 overflow-x-auto">
                {JSON.stringify(toolInput, null, 2)}
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
