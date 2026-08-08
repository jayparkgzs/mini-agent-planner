# agent/core.py
import json
from typing import Dict, List
from openai import OpenAI

from .tools import registry
from .planner import TaskPlanner


class ReActAgent:
    """
    ReAct Agent 核心引擎
    循环：LLM 思考 → 调用工具 → 观察结果 → 继续思考 ...
    """
    
    def __init__(self, api_key: str, base_url: str = None, model: str = "gpt-3.5-turbo"):
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
        self.model = model
        self.planner = TaskPlanner()
        self.pending_confirm = None
        self.history = []
    
    def run(self, user_input: str) -> Dict:
        if self.pending_confirm:
            return {
                "status": "need_confirm",
                "result": "有未确认的操作，请先处理",
                "pending": self.pending_confirm
            }
        
        plan = self.planner.plan(user_input)
        plan_text = "\n".join([
            f"步骤 {p['step']}: 使用 {p['tool']} - {p['reason']}"
            for p in plan
        ])
        
        system_prompt = self._build_system_prompt(plan_text)
        messages = [{"role": "system", "content": system_prompt}]
        
        for h in self.history[-5:]:
            messages.append({"role": "user", "content": h["user"]})
            messages.append({"role": "assistant", "content": h["assistant"]})
        
        messages.append({"role": "user", "content": user_input})
        
        max_steps = 10
        for step in range(max_steps):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=registry.get_schemas(),
                tool_choice="auto",
                temperature=0.3
            )
            
            message = response.choices[0].message
            
            if not message.tool_calls:
                answer = message.content
                self.history.append({"user": user_input, "assistant": answer})
                return {
                    "status": "completed",
                    "result": answer,
                    "steps": step + 1
                }
            
            tool_call = message.tool_calls[0]
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            if tool_name == "write_file":
                self.pending_confirm = {
                    "tool": tool_name,
                    "args": arguments,
                    "reason": f"即将写入文件 '{arguments.get('filename')}'"
                }
                return {
                    "status": "need_confirm",
                    "result": f"即将写入文件 '{arguments.get('filename')}'，请确认",
                    "pending": self.pending_confirm
                }
            
            observation = registry.execute(tool_name, arguments)
            
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": tool_call.function.arguments
                    }
                }]
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": observation
            })
        
        return {
            "status": "error",
            "result": "执行步数超过限制，任务未完成"
        }
    
    def confirm(self, confirm: bool) -> Dict:
        if not self.pending_confirm:
            return {"status": "error", "result": "没有待确认的操作"}
        
        if confirm:
            result = registry.execute(
                self.pending_confirm["tool"],
                self.pending_confirm["args"]
            )
            self.pending_confirm = None
            return {
                "status": "completed",
                "result": f"已确认执行：{result}"
            }
        else:
            self.pending_confirm = None
            return {
                "status": "completed",
                "result": "已取消操作"
            }
    
    def _build_system_prompt(self, plan_text: str) -> str:
        tools_desc = []
        for schema in registry.get_schemas():
            func = schema["function"]
            tools_desc.append(f"- {func['name']}: {func['description']}")
        
        return f"""你是一个智能任务执行助手。你的目标是完成用户请求，必须通过调用工具来执行操作。

可用工具：
{chr(10).join(tools_desc)}

执行计划：
{plan_text}

规则：
1. 分析用户需要什么
2. 如果需要调用工具（如查天气、写文件、计算），必须调用对应工具，不要口头描述
3. 调用工具后，观察结果，继续下一步
4. 所有操作完成后，给出最终答案
5. 当需要写入文件时，直接调用 write_file 工具，系统会自动处理安全确认
"""
