"""Agent 執行腳本 - 在專案容器內運行"""
import os
import logging
from deep_agent import RefactorAgent
from models import AnthropicModelProvider
from mongodb_client import MongoDBClient

logger = logging.getLogger(__name__)


class CloudRun:
    """CloudRun - 透過 MongoDB 取得 init_prompt 並執行 RefactorAgent
    
    使用方式:
        cloudrun = CloudRun(run_id="xxx", mongodb_url="mongodb://localhost:27017")
        cloudrun.run()
    """
    
    def __init__(self, run_id: str, mongodb_url: str):
        """初始化 CloudRun
        
        Args:
            run_id: agent_runs collection 的 _id
            mongodb_url: MongoDB 連線 URL
        """
        self.run_id = run_id
        self.mongodb_url = mongodb_url
        self.mongo_client = MongoDBClient(mongodb_url)
        
        # 取得 agent_run 資料
        self.agent_run = self.mongo_client.get_agent_run(run_id)
        if not self.agent_run:
            raise ValueError(f"AgentRun 不存在: {run_id}")
        
        # 取得 project 資料（含 init_prompt）
        project_id = self.agent_run['project_id']
        self.project = self.mongo_client.get_project(project_id)
        if not self.project:
            raise ValueError(f"Project 不存在: {project_id}")
        
        self.init_prompt = self.project.get('init_prompt', '')
        logger.info(f"CloudRun 初始化完成: run_id={run_id}, project_id={project_id}")
    
    def run(self, verbose: bool = True):
        """執行 RefactorAgent
        
        Args:
            verbose: 是否顯示詳細的 chunk 解析資訊
        """
        # 初始化 LLM
        provider = AnthropicModelProvider()
        model = provider.get_model()
        
        # 建立 RefactorAgent
        agent = RefactorAgent(model, verbose=verbose)
        
        # 使用 init_prompt 執行 agent
        logger.info(f"開始執行 Agent: {self.init_prompt[:100]}...")
        agent.run(user_message=self.init_prompt)
        
        # 關閉 MongoDB 連線
        self.mongo_client.close()


if __name__ == "__main__":
    # 從環境變數取得參數
    run_id = os.getenv("RUN_ID")
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    
    if run_id:
        # 使用 CloudRun（從 MongoDB 取得 init_prompt）
        cloudrun = CloudRun(run_id=run_id, mongodb_url=mongodb_url)
        cloudrun.run()
    else:
        # 本地測試模式（直接執行）
        provider = AnthropicModelProvider()
        model = provider.get_model()
        agent = RefactorAgent(model, verbose=True)
        
        message = """
        檢視我的資料夾結構，並整理一個將此專案重構成 typescript 的計畫，並將檔案寫入 ./memory/plan.md 檔案
        """
        agent.run(user_message=message)
