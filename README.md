# Mini Agent Planner 🤖

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

&gt; 一个基于 **ReAct 范式** 的 Agent 平台原型，支持任务规划、工具调用、Human-in-the-loop、多 Agent 协作与自动化评测。

## ✨ 核心特性

- **🧠 ReAct 决策引擎**：支持 Thought → Action → Observation 循环，任务完成率 100%（测试集）
- **🛡️ Human-in-the-loop**：敏感操作（文件写入）前自动暂停，等待用户确认
- **💾 分层记忆架构**：热记忆（上下文）+ 温记忆（JSON 持久化），支持跨会话记忆
- **🤝 多 Agent 协作**：Orchestrator-Workers 模式，并行执行安全/性能/规范审查
- **📊 自动化评测**：量化工具调用准确率、任务成功率、Token 成本
- **🔍 可观测性**：完整调用链追踪（Tracer）+ 自动故障诊断（Debugger）

## 🚀 快速开始

### 安装依赖

```bash
git clone https://github.com/你的用户名/mini-agent-planner.git
cd mini-agent-planner
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt