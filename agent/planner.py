# agent/planner.py
from typing import List, Dict


class TaskPlanner:
    """
    任务规划器：把用户指令拆解为执行步骤
    目前用简单规则，后续可升级为大模型拆解
    """
    
    def plan(self, user_input: str) -> List[Dict]:
        """分析用户输入，返回执行计划"""
        plan = []
        step = 1
        
        # 如果提到天气，先查天气
        if "天气" in user_input:
            plan.append({
                "step": step,
                "tool": "search_weather",
                "reason": "用户需要查询天气信息",
                "needs_confirm": False
            })
            step += 1
        
        # 如果提到计算，用计算器
        if any(kw in user_input for kw in ["计算", "等于", "多少", "+", "-", "*", "/"]):
            plan.append({
                "step": step,
                "tool": "calculator",
                "reason": "用户需要数学计算",
                "needs_confirm": False
            })
            step += 1
        
        # 如果提到写/保存/记录，需要写入文件（标记需要确认）
        if any(kw in user_input for kw in ["写", "保存", "记录", "写入", "放进", "存到"]):
            plan.append({
                "step": step,
                "tool": "write_file",
                "reason": "用户需要将结果写入文件",
                "needs_confirm": True
            })
            step += 1
        
        # 如果没有任何匹配，直接回答
        if not plan:
            plan.append({
                "step": 1,
                "tool": "direct_answer",
                "reason": "无需工具，直接回答",
                "needs_confirm": False
            })
        
        return plan