import { useEffect, useState, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { getProjectAPI, provisionProjectAPI } from "@/services/project.service";
import {
  sendChatMessageAPI,
  streamChatResponseAPI,
  stopChatAPI,
} from "@/services/chat.service";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import type { Project } from "@/types/project.types";
import type { ChatMessage, ChatStreamEvent } from "@/types/chat.types";
import {
  Send,
  StopCircle,
  ChevronRight,
  Bot,
  User,
  Wrench,
  Loader2,
  RefreshCw,
} from "lucide-react";
import ReactMarkdown from "react-markdown";

// 狀態顏色映射
const statusColors: Record<
  string,
  "default" | "secondary" | "destructive" | "success" | "warning"
> = {
  CREATED: "secondary",
  PROVISIONING: "warning",
  READY: "success",
  RUNNING: "default",
  STOPPED: "secondary",
  FAILED: "destructive",
};

export default function ChatPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [provisioning, setProvisioning] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const cancelStreamRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (id) {
      loadProject();
    }
  }, [id]);

  // 自動滾動到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadProject = async () => {
    try {
      const data = await getProjectAPI(id!);
      setProject(data);
    } catch (error) {
      console.error("載入專案失敗", error);
    } finally {
      setLoading(false);
    }
  };

  const handleProvision = async () => {
    try {
      setProvisioning(true);
      await provisionProjectAPI(id!);
      await loadProject();
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      alert(err.response?.data?.detail || "Provision 失敗");
    } finally {
      setProvisioning(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsStreaming(true);

    // 建立一個暫時的 assistant 訊息用於串流顯示
    const assistantMessageId = `assistant-${Date.now()}`;
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, assistantMessage]);

    try {
      // 發送訊息
      const response = await sendChatMessageAPI(
        id!,
        userMessage.content,
        threadId || undefined,
      );
      setCurrentTaskId(response.task_id);
      setThreadId(response.thread_id);

      // 串流接收回應
      const cancelFn = await streamChatResponseAPI(
        id!,
        response.task_id,
        (event: ChatStreamEvent) => {
          handleStreamEvent(event, assistantMessageId);
        },
        (error) => {
          console.error("串流錯誤:", error);
          setIsStreaming(false);
        },
      );
      cancelStreamRef.current = cancelFn;
    } catch (error: unknown) {
      console.error("發送訊息失敗:", error);
      const err = error as { response?: { data?: { detail?: string } } };
      // 更新 assistant 訊息顯示錯誤
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: `錯誤: ${err.response?.data?.detail || "發送失敗"}`,
              }
            : msg,
        ),
      );
      setIsStreaming(false);
    }
  };

  const handleStreamEvent = (
    event: ChatStreamEvent,
    assistantMessageId: string,
  ) => {
    switch (event.type) {
      case "text_delta":
        // 累加文字到 assistant 訊息（舊格式）
        if (
          event.content &&
          typeof event.content === "object" &&
          "delta" in event.content
        ) {
          const delta = (event.content as { delta?: string }).delta || "";
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: msg.content + delta }
                : msg,
            ),
          );
        }
        break;

      case "ai_content":
        // 累加文字到 assistant 訊息（ChunkParser 格式）
        if (
          event.content &&
          typeof event.content === "object" &&
          "content" in event.content
        ) {
          const content = (event.content as { content?: string }).content || "";
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: msg.content + content }
                : msg,
            ),
          );
        }
        break;

      case "tool_call_start":
        // 新增工具呼叫訊息（舊格式）
        if (event.content) {
          const toolMessage: ChatMessage = {
            id: `tool-${Date.now()}`,
            role: "tool",
            content: "",
            timestamp: new Date().toISOString(),
            toolName: (event.content as { name?: string }).name,
            toolInput: event.content as Record<string, unknown>,
          };
          // 直接追加到訊息列表末端
          setMessages((prev) => [...prev, toolMessage]);
        }
        break;

      case "tool_calls":
        // 工具呼叫（ChunkParser 格式）
        if (event.content && "tool_calls" in event.content) {
          const toolCalls = (
            event.content as {
              tool_calls: Array<{
                name: string;
                id: string;
                args: Record<string, unknown>;
              }>;
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
          // 直接追加到訊息列表末端，保持順序
          setMessages((prev) => [...prev, ...toolMessages]);
        }
        break;

      case "tool_call_result":
        // 更新最近的工具呼叫結果（舊格式）
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
        // 工具執行結果（ChunkParser 格式）
        if (event.content && "results" in event.content) {
          const results = (
            event.content as {
              results: Array<{
                name: string;
                tool_call_id: string;
                content: string;
              }>;
            }
          ).results;
          // 更新對應的工具呼叫訊息
          setMessages((prev) => {
            const newMessages = [...prev];
            for (const result of results) {
              // 優先使用 tool_call_id 匹配，否則使用 name 匹配
              const toolIdx = newMessages.findIndex(
                (m) =>
                  m.role === "tool" &&
                  (m.toolCallId === result.tool_call_id ||
                    (m.toolName === result.name && !m.toolOutput)),
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
        }
        break;

      case "token_usage":
        // 更新 token 使用統計
        if (event.content) {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    tokenUsage: event.content as ChatMessage["tokenUsage"],
                  }
                : msg,
            ),
          );
        }
        break;

      case "status":
        // 檢查任務是否完成
        if (event.content) {
          const status = (event.content as { status?: string }).status;
          if (
            status === "success" ||
            status === "failed" ||
            status === "stopped"
          ) {
            setIsStreaming(false);
            cancelStreamRef.current = null;
          }
        }
        break;

      case "log":
        // 處理一般日誌（可能包含文字輸出）
        if (event.message) {
          // 嘗試提取文字內容
          const match = event.message.match(/\[text_delta\]\s*(.+)/);
          if (match) {
            try {
              const data = JSON.parse(match[1]);
              if (data.delta) {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: msg.content + data.delta }
                      : msg,
                  ),
                );
              }
            } catch {
              // 忽略解析錯誤
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
        await stopChatAPI(id!, currentTaskId);
      } catch (error) {
        console.error("停止聊天失敗:", error);
      }
    }
    setIsStreaming(false);
  };

  const projectName =
    project?.repo_url?.split("/").pop()?.replace(".git", "") ||
    (project?.project_type === "SANDBOX" ? "Sandbox" : "Project");

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-lg text-gray-300">載入中...</div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-lg text-gray-300">專案不存在</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 flex flex-col">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm">
            <Link
              to="/projects"
              className="flex items-center gap-2 text-gray-400 hover:text-gray-200"
            >
              <div className="w-6 h-6 bg-orange-500 rounded flex items-center justify-center text-white text-xs font-bold">
                smo
              </div>
              <span>AI 舊程式碼智能重構系統</span>
            </Link>
            <ChevronRight className="w-4 h-4 text-gray-600" />
            <Link
              to={`/projects/${id}`}
              className="text-gray-400 hover:text-gray-200"
            >
              {projectName}
            </Link>
            <ChevronRight className="w-4 h-4 text-gray-600" />
            <span className="text-gray-200">Chat</span>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant={statusColors[project.status]}>
              {project.status}
            </Badge>
            <span className="text-sm text-gray-400">
              {user?.username || user?.email}
            </span>
          </div>
        </div>
      </header>

      {/* Provision 提示 */}
      {project.status === "CREATED" && (
        <div className="bg-yellow-900/20 border-b border-yellow-700/50 px-6 py-3">
          <div className="flex items-center justify-between">
            <span className="text-yellow-400">
              專案尚未 Provision，請先建立容器環境才能開始聊天
            </span>
            <Button onClick={handleProvision} disabled={provisioning} size="sm">
              {provisioning ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Provisioning...
                </>
              ) : (
                "Provision 專案"
              )}
            </Button>
          </div>
        </div>
      )}

      {/* Thread ID 顯示 */}
      {threadId && (
        <div className="bg-gray-800/50 border-b border-gray-700 px-6 py-2">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>Thread ID:</span>
            <code className="bg-gray-800 px-2 py-0.5 rounded">{threadId}</code>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2"
              onClick={() => {
                setThreadId(null);
                setMessages([]);
              }}
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              新對話
            </Button>
          </div>
        </div>
      )}

      {/* 聊天訊息區域 */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Bot className="w-16 h-16 mb-4 opacity-50" />
            <p className="text-lg">開始與 AI Agent 對話</p>
            <p className="text-sm mt-2">
              輸入訊息讓 Agent 幫你探索和操作工作空間
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {msg.role !== "user" && (
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  msg.role === "tool" ? "bg-yellow-900/50" : "bg-purple-900/50"
                }`}
              >
                {msg.role === "tool" ? (
                  <Wrench className="w-4 h-4 text-yellow-400" />
                ) : (
                  <Bot className="w-4 h-4 text-purple-400" />
                )}
              </div>
            )}

            <div
              className={`max-w-[70%] rounded-lg p-4 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : msg.role === "tool"
                    ? "bg-yellow-900/30 border border-yellow-700/50"
                    : "bg-gray-800 border border-gray-700"
              }`}
            >
              {msg.role === "tool" ? (
                <>
                  <div className="text-sm text-blue-400 font-mono mb-2">
                    {msg.toolName}
                  </div>
                  {msg.toolInput && Object.keys(msg.toolInput).length > 0 && (
                    <details className="mb-2">
                      <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                        參數
                      </summary>
                      <pre className="text-xs text-gray-400 mt-1 overflow-x-auto">
                        {JSON.stringify(msg.toolInput, null, 2)}
                      </pre>
                    </details>
                  )}
                  {msg.toolOutput ? (
                    <pre className="text-xs text-gray-300 whitespace-pre-wrap overflow-x-auto max-h-60 overflow-y-auto">
                      {msg.toolOutput}
                    </pre>
                  ) : (
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      執行中...
                    </div>
                  )}
                </>
              ) : (
                <div className="text-sm prose prose-invert prose-sm max-w-none">
                  {msg.content ? (
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  ) : (
                    msg.role === "assistant" &&
                    isStreaming && (
                      <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse" />
                    )
                  )}
                </div>
              )}

              {msg.tokenUsage && (
                <div className="mt-2 text-xs text-gray-500">
                  Tokens: {msg.tokenUsage.input_tokens} in /{" "}
                  {msg.tokenUsage.output_tokens} out
                </div>
              )}
            </div>

            {msg.role === "user" && (
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4 text-white" />
              </div>
            )}
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* 輸入區域 */}
      <div className="border-t border-gray-800 p-4 bg-gray-900">
        <div className="flex gap-3 items-end">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder={
              project.status !== "READY"
                ? "請先 Provision 專案..."
                : "輸入訊息... (Enter 發送, Shift+Enter 換行)"
            }
            disabled={isStreaming || project.status !== "READY"}
            className="flex-1 min-h-[60px] max-h-[200px] resize-none"
            rows={2}
          />
          {isStreaming ? (
            <Button
              onClick={stopChat}
              variant="destructive"
              size="lg"
              className="px-6"
            >
              <StopCircle className="w-5 h-5" />
            </Button>
          ) : (
            <Button
              onClick={sendMessage}
              disabled={!input.trim() || project.status !== "READY"}
              size="lg"
              className="px-6"
            >
              <Send className="w-5 h-5" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
