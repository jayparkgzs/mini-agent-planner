import json
import time
import uuid
from typing import Dict, List
from openai import OpenAI

from .tools import registry
from .planner import TaskPlanner
from memory.short_term import ShortTermMemory
from observability.tracer import tracer
from observability.debugger import AgentDebugger


class ReActAgent:
    """
    ReAct Agent 核心引擎（第4周升级版：接入调用链追踪与故障诊断）
    """

    def __init__(self, api_key: str, base_url: str = None, model: str = "gpt-3.5-turbo"):
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
        self.model = model
        self.planner = TaskPlanner()
        self.memory = ShortTermMemory(session_id="default")
        self.debugger = AgentDebugger()
        self.pending_confirm = None
        self.history = []

    def run(self, user_input: str) -> Dict:
        # ========== 追踪：开始 ==========
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        tracer.start_trace(task_id, user_input)

        self.memory.add("user", user_input)

        if self.pending_confirm:
            tracer.end_trace("need_confirm", "有未确认的操作", 0)
            return {
                "status": "need_confirm",
                "result": "有未确认的操作，请先处理",
                "pending": self.pending_confirm,
                "trace_id": task_id
            }

        plan = self.planner.plan(user_input)
        plan_text = "\n".join([
            f"步骤 {p['step']}: 使用 {p['tool']} - {p['reason']}"
            for p in plan
        ])

        system_prompt = self._build_system_prompt(plan_text)
        messages = [{"role": "system", "content": system_prompt}]

        recent_memory = self.memory.get_recent(10)
        for msg in recent_memory:
            if msg["role"] == "user":
                messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                messages.append({"role": "assistant", "content": msg["content"]})

        if not recent_memory or recent_memory[-1]["content"] != user_input:
            messages.append({"role": "user", "content": user_input})

        max_steps = 10

        for step in range(max_steps):
            step_start = time.time()

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=registry.get_schemas(),
                    tool_choice="auto",
                    temperature=0.3
                )
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                tracer.end_trace("error", f"LLM API 错误: {str(e)}", duration)
                return {
                    "status": "error",
                    "result": f"LLM 调用失败: {str(e)}",
                    "trace_id": task_id
                }

            message = response.choices[0].message

            # ========== 情况 A：直接给出答案 ==========
            if not message.tool_calls:
                answer = message.content
                self.memory.add("assistant", answer)
                self.history.append({"user": user_input, "assistant": answer})

                duration = (time.time() - start_time) * 1000
                tracer.end_trace("completed", answer, duration)

                return {
                    "status": "completed",
                    "result": answer,
                    "steps": step + 1,
                    "trace_id": task_id
                }

            # ========== 情况 B：调用工具 ==========
            tool_call = message.tool_calls[0]
            tool_name = tool_call.function.name

            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as e:
                duration = (time.time() - start_time) * 1000
                tracer.end_trace("error", f"参数解析失败: {str(e)}", duration)
                return {
                    "status": "error",
                    "result": f"工具参数解析失败: {str(e)}",
                    "trace_id": task_id
                }

            # 记录决策步骤（Thought + Action）
            tracer.log_step(
                step_num=step + 1,
                thought=f"分析用户需求，决定调用工具: {tool_name}",
                action="tool_call",
                tool_name=tool_name,
                arguments=arguments
            )

            # Human-in-the-loop：写入文件前暂停
            if tool_name == "write_file":
                self.pending_confirm = {
                    "tool": tool_name,
                    "args": arguments,
                    "reason": f"即将写入文件 '{arguments.get('filename')}'"
                }

                duration = (time.time() - start_time) * 1000
                tracer.end_trace("need_confirm", "等待用户确认文件写入", duration)

                return {
                    "status": "need_confirm",
                    "result": f"即将写入文件 '{arguments.get('filename')}'，请确认",
                    "pending": self.pending_confirm,
                    "trace_id": task_id
                }

            # 执行工具
            observation = registry.execute(tool_name, arguments)

            # 记录观察结果
            tracer.log_step(
                step_num=step + 1,
                thought="观察工具执行结果",
                action="observe",
                observation=observation
            )

            # 将工具调用和观察结果加入上下文
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

        # ========== 超过最大步数 ==========
        duration = (time.time() - start_time) * 1000
        tracer.end_trace("error", "执行步数超过限制，任务未完成", duration)

        return {
            "status": "error",
            "result": "执行步数超过限制，任务未完成",
            "trace_id": task_id
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