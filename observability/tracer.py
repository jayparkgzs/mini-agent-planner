import json
import time
from typing import Dict, List
from datetime import datetime


class AgentTracer:
    """
    Agent 调用链追踪器
    记录每次 ReAct 循环的完整轨迹：Thought → Action → Observation
    """
    
    def __init__(self):
        self.traces: List[Dict] = []
        self.current_trace = None
    
    def start_trace(self, task_id: str, user_input: str):
        """开始追踪一个新任务"""
        self.current_trace = {
            "trace_id": task_id,
            "start_time": datetime.now().isoformat(),
            "user_input": user_input,
            "steps": [],
            "status": "running"
        }
    
    def log_step(self, step_num: int, thought: str, action: str, 
                 tool_name: str = None, arguments: Dict = None,
                 observation: str = None, error: str = None):
        """记录一步的完整信息"""
        step = {
            "step": step_num,
            "timestamp": time.time(),
            "thought": thought,
            "action": action,
            "tool_name": tool_name,
            "arguments": arguments,
            "observation": observation,
            "error": error,
            "duration_ms": None
        }
        self.current_trace["steps"].append(step)
        return step
    
    def end_trace(self, status: str, result: str, duration_ms: float):
        """结束追踪"""
        if self.current_trace:
            self.current_trace["status"] = status
            self.current_trace["result"] = result
            self.current_trace["duration_ms"] = duration_ms
            self.current_trace["end_time"] = datetime.now().isoformat()
            self.traces.append(self.current_trace)
            self.current_trace = None
    
    def get_last_trace(self) -> Dict:
        """获取最近一次追踪"""
        if self.traces:
            return self.traces[-1]
        return {}
    
    def get_failure_traces(self) -> List[Dict]:
        """获取所有失败的追踪"""
        return [t for t in self.traces if t["status"] in ["error", "failed"]]
    
    def export(self, filename: str = "traces.json"):
        """导出追踪记录"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.traces, f, ensure_ascii=False, indent=2)
        return filename


# 全局追踪器
tracer = AgentTracer()