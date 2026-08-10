# benchmark/evaluator.py
import time
import json
from typing import Dict, List
from dataclasses import dataclass, asdict


@dataclass
class EvalResult:
    """单次评测结果"""
    task_name: str
    success: bool
    steps: int
    tool_calls: int
    correct_tools: int
    duration_ms: float
    token_cost: float  # 估算


class AgentEvaluator:
    """
    Agent 评测器：量化工具调用准确率、任务完成率等
    """
    
    def __init__(self):
        self.results: List[EvalResult] = []
    
    def record(self, result: EvalResult):
        self.results.append(result)
    
    def get_summary(self) -> Dict:
        """生成评测摘要"""
        total = len(self.results)
        if total == 0:
            return {"error": "没有评测数据"}
        
        success_count = sum(1 for r in self.results if r.success)
        total_tools = sum(r.tool_calls for r in self.results)
        correct_tools = sum(r.correct_tools for r in self.results)
        total_duration = sum(r.duration_ms for r in self.results)
        
        return {
            "total_tasks": total,
            "success_rate": success_count / total,
            "tool_accuracy": correct_tools / total_tools if total_tools > 0 else 0,
            "avg_duration_ms": total_duration / total,
            "total_cost": sum(r.token_cost for r in self.results),
            "details": [asdict(r) for r in self.results]
        }
    
    def save_report(self, filename: str = "benchmark_report.json"):
        """保存评测报告"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.get_summary(), f, ensure_ascii=False, indent=2)
        return filename


# 测试用例定义
BENCHMARK_TASKS = [
    {
        "name": "天气查询",
        "input": "北京天气怎么样",
        "expected_tools": ["search_weather"],
        "expected_in_result": ["晴天", "多云", "雨"]
    },
    {
        "name": "数学计算",
        "input": "计算 2+3*4",
        "expected_tools": ["calculator"],
        "expected_in_result": ["14"]
    },
    {
        "name": "多步任务",
        "input": "查一下上海天气，然后写进 shanghai.txt",
        "expected_tools": ["search_weather", "write_file"],
        "expected_in_result": []
    }
]