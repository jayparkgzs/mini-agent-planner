# scheduler/orchestrator.py
from typing import Dict, List, Callable


class SubAgent:
    """子 Agent 定义"""
    
    def __init__(self, name: str, description: str, handler: Callable):
        self.name = name
        self.description = description
        self.handler = handler


class Orchestrator:
    """
    主调度器：识别任务类型，派发给对应的子 Agent
    """
    
    def __init__(self):
        self.agents: Dict[str, SubAgent] = {}
    
    def register(self, agent: SubAgent):
        """注册子 Agent"""
        self.agents[agent.name] = agent
    
    def dispatch(self, task_type: str, context: Dict) -> Dict:
        """派发任务给子 Agent"""
        agent = self.agents.get(task_type)
        if not agent:
            return {
                "status": "error",
                "result": f"未找到处理 '{task_type}' 的子 Agent"
            }
        
        try:
            result = agent.handler(context)
            return {
                "status": "completed",
                "result": result,
                "agent": task_type
            }
        except Exception as e:
            return {
                "status": "error",
                "result": str(e),
                "agent": task_type
            }
    
    def list_agents(self) -> List[Dict]:
        """列出所有可用子 Agent"""
        return [
            {"name": a.name, "description": a.description}
            for a in self.agents.values()
        ]


# 全局调度器实例
orchestrator = Orchestrator()
