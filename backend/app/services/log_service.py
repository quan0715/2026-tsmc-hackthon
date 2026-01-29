"""日誌服務層"""
import subprocess
import asyncio
import logging
from typing import AsyncGenerator
import json

logger = logging.getLogger(__name__)


class LogService:
    """日誌服務 (使用 subprocess 串流 Docker logs)"""

    async def stream_container_logs(
        self,
        container_id: str,
        follow: bool = True,
        tail: int = 100,
    ) -> AsyncGenerator[str, None]:
        """串流容器日誌 (SSE 格式)"""
        try:
            # 建立 docker logs 指令
            cmd = ["docker", "logs"]

            if follow:
                cmd.append("-f")  # Follow log output

            if tail > 0:
                cmd.extend(["--tail", str(tail)])

            cmd.append(container_id)

            # 啟動 subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,  # 合併 stderr 到 stdout
            )

            logger.info(f"開始串流容器日誌: {container_id}")

            # 串流輸出
            line_count = 0
            last_ping = asyncio.get_event_loop().time()

            while True:
                # 檢查是否需要發送 ping (每 30 秒)
                current_time = asyncio.get_event_loop().time()
                if current_time - last_ping > 30:
                    yield f"event: ping\ndata: {json.dumps({'timestamp': current_time})}\n\n"
                    last_ping = current_time

                # 讀取一行 (設定超時避免永久阻塞)
                try:
                    line = await asyncio.wait_for(
                        process.stdout.readline(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    # 超時後繼續循環 (用於發送 ping)
                    if not follow:
                        break
                    continue

                if not line:
                    # 沒有更多輸出
                    break

                # 解碼並發送日誌行
                log_line = line.decode("utf-8").rstrip()
                if log_line:
                    line_count += 1
                    yield f"data: {json.dumps({'line': log_line, 'number': line_count})}\n\n"

            # 等待 process 結束
            await process.wait()

            logger.info(f"日誌串流結束: {container_id}, 共 {line_count} 行")

            # 發送結束事件
            yield f"event: end\ndata: {json.dumps({'total_lines': line_count})}\n\n"

        except Exception as e:
            error_msg = f"串流日誌失敗: {str(e)}"
            logger.error(error_msg)
            yield f"event: error\ndata: {json.dumps({'error': error_msg})}\n\n"

        finally:
            # 清理 process
            if process and process.returncode is None:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except Exception as e:
                    logger.warning(f"清理 process 失敗: {e}")
