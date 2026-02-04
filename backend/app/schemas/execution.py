"""執行指令 API Schema"""
from pydantic import BaseModel, Field
from typing import Optional


class ExecCommandRequest(BaseModel):
    """執行指令請求"""

    command: str = Field(..., description="要執行的指令")
    workdir: Optional[str] = Field(
        default="/workspace/repo", description="工作目錄"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "command": "ls -la",
                "workdir": "/workspace/repo",
            }
        }


class ExecCommandResponse(BaseModel):
    """執行指令回應"""

    exit_code: int = Field(..., description="退出代碼")
    stdout: str = Field(..., description="標準輸出")
    stderr: str = Field(..., description="標準錯誤")

    class Config:
        json_schema_extra = {
            "example": {
                "exit_code": 0,
                "stdout": "total 4\ndrwxr-xr-x 3 root root  96 Jan 29 16:59 .\n",
                "stderr": "",
            }
        }
