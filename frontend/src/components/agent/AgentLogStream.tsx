import { useEffect, useState, useRef } from "react";
import { streamAgentLogsAPI } from "@/services/agent.service";
import type { AgentLogEvent } from "@/types/agent.types";
import type { Task } from "./TaskList";
import { Bot, Wrench, Terminal, CheckCircle, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface Props {
  projectId: string;
  runId: string;
  autoStart?: boolean;
  onTasksUpdate?: (tasks: Task[]) => void;
}

export function AgentLogStream({
  projectId,
  runId,
  autoStart = true,
  onTasksUpdate,
}: Props) {
  const [logs, setLogs] = useState<AgentLogEvent[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cancelStreamRef = useRef<(() => void) | null>(null);
  const isMountedRef = useRef(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    isMountedRef.current = true;
    if (autoStart) {
      startStream();
    } else {
      if (cancelStreamRef.current) {
        cancelStreamRef.current();
        cancelStreamRef.current = null;
        setIsStreaming(false);
      }
    }
    return () => {
      isMountedRef.current = false;
      if (cancelStreamRef.current) {
        cancelStreamRef.current();
        cancelStreamRef.current = null;
      }
    };
  }, [runId, autoStart]);

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  const startStream = async () => {
    if (cancelStreamRef.current) {
      cancelStreamRef.current();
      cancelStreamRef.current = null;
    }

    setIsStreaming(true);
    setError(null);
    setLogs([]);

    try {
      const cancelFn = await streamAgentLogsAPI(
        projectId,
        runId,
        (event) => {
          if (!isMountedRef.current) return;
          setLogs((prev) => [...prev, event]);

          if (
            (event.type === "task_list" || event.type === "todo_update") &&
            event.content?.tasks
          ) {
            onTasksUpdate?.(event.content.tasks);
          }

          if (event.type === "tools_execution" && event.content?.results) {
            for (const result of event.content.results) {
              if (result.name === "write_todos" && result.content) {
                const match = result.content.match(
                  /Updated todo list to (\[.*\])/,
                );
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
                    console.warn("解析 write_todos 結果失敗", e);
                  }
                }
              }
            }
          }
        },
        (err) => {
          setError(err.message);
          setIsStreaming(false);
        },
      );
      cancelStreamRef.current = cancelFn;
    } catch (err: any) {
      setError(err.message);
      setIsStreaming(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {error && (
        <div className="text-red-400 px-4 py-2 text-sm border-b border-gray-800">
          {error}
        </div>
      )}

      <div
        ref={logsContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-3"
      >
        {logs.length === 0 ? (
          <div className="text-gray-500 text-center py-8 text-sm">
            {isStreaming ? "等待回應..." : "尚無日誌"}
          </div>
        ) : (
          logs.map((log, idx) => <LogEntry key={idx} event={log} />)
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
}

function LogEntry({ event }: { event: AgentLogEvent }) {
  const { type, message, content } = event;

  // AI 內容 - 主要文字輸出
  if (type === "ai_content" || type === "llm_response") {
    const text = content?.content || message || "";
    if (!text) return null;
    return (
      <div className="flex gap-3">
        <Bot className="w-4 h-4 text-purple-400 mt-1 flex-shrink-0" />
        <div className="text-sm text-gray-200 prose prose-invert prose-sm max-w-none">
          <ReactMarkdown>{text}</ReactMarkdown>
        </div>
      </div>
    );
  }

  // 工具調用
  if (type === "tool_calls" || type === "tool_call") {
    const calls = content?.tool_calls || [];
    if (calls.length === 0) return null;
    return (
      <div className="space-y-2">
        {calls.map((call: any, idx: number) => (
          <ToolCallEntry key={idx} call={call} />
        ))}
      </div>
    );
  }

  // 工具執行結果
  if (type === "tools_execution" || type === "tool_result") {
    const results = content?.results || [];
    if (results.length === 0) return null;
    return (
      <div className="space-y-2">
        {results.map((result: any, idx: number) => (
          <ToolResultEntry key={idx} result={result} />
        ))}
      </div>
    );
  }

  // 一般日誌訊息
  if (type === "log" && message) {
    // 過濾掉系統訊息
    if (
      message.startsWith("[") ||
      message.includes("初始化") ||
      message.includes("建立")
    ) {
      return null;
    }
    return <div className="text-xs text-gray-500">{message}</div>;
  }

  // 狀態更新
  if (type === "status") {
    const status = content?.status;
    if (status === "success") {
      return (
        <div className="flex items-center gap-2 text-sm text-green-400">
          <CheckCircle className="w-4 h-4" />
          <span>執行完成</span>
        </div>
      );
    }
    return null;
  }

  // 其他類型忽略
  return null;
}

function ToolCallEntry({ call }: { call: any }) {
  const toolName = call.name || call.function?.name || "未知工具";
  const args = call.args || call.function?.arguments || {};

  return (
    <div className="flex gap-3">
      <Wrench className="w-4 h-4 text-blue-400 mt-1 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="text-sm text-blue-400 font-mono">{toolName}</div>
        {Object.keys(args).length > 0 && (
          <details className="mt-1">
            <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
              參數
            </summary>
            <pre className="text-xs text-gray-400 mt-1 overflow-x-auto">
              {JSON.stringify(args, null, 2)}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
}

function ToolResultEntry({ result }: { result: any }) {
  const toolName = result.name || result.tool_name || "未知";
  const output = result.content || result.output || "";
  const isLoading = !output;

  return (
    <div className="flex gap-3">
      <Terminal className="w-4 h-4 text-cyan-400 mt-1 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="text-sm text-cyan-400 font-mono">{toolName}</div>
        {isLoading ? (
          <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
            <Loader2 className="w-3 h-3 animate-spin" />
            執行中...
          </div>
        ) : (
          <pre className="text-xs text-gray-400 mt-1 whitespace-pre-wrap overflow-x-auto max-h-40 overflow-y-auto">
            {typeof output === "string"
              ? output
              : JSON.stringify(output, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
