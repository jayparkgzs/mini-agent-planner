# Mini Agent Planner 架构设计

## 1. 整体架构

## 2. 核心模块

### 2.1 ReAct 循环引擎 (agent/core.py)
- **ReAct 范式**：Thought → Action → Observation → ... → Answer
- **Human-in-the-loop**：敏感操作（如文件写入）前暂停，等待用户确认
- **记忆接入**：每次对话自动保存到 ShortTermMemory

### 2.2 任务规划器 (agent/planner.py)
- 基于规则的任务拆解（后续升级为 LLM 规划）
- 识别关键词，匹配对应工具

### 2.3 工具注册中心 (agent/tools.py)
- 装饰器模式注册工具
- 统一 schema 定义，供 LLM 识别
- 当前工具：search_weather, calculator, read_file, write_file

### 2.4 记忆模块 (memory/short_term.py)
- **热记忆**：当前会话上下文（内存中）
- **温记忆**：JSON 文件持久化
- 支持按轮数检索历史对话

### 2.5 上下文管理 (context/manager.py)
- Token 预算控制（默认 4000 tokens）
- 滑动窗口策略：保留系统提示 + 最近 N 轮 + 当前输入
- 超出预算时自动截断旧对话

### 2.6 调度器 (scheduler/orchestrator.py)
- Orchestrator-Workers 模式
- 主 Agent 识别任务类型，派发给子 Agent
- 每个子 Agent 有独立上下文

## 3. 数据流

## 4. 安全设计

- **文件写入确认**：write_file 操作必须用户确认（Y/N）
- **Token 上限**：防止上下文爆炸导致 API 费用激增
- **执行步数限制**：最多 10 步，防止无限循环

## 5. 扩展计划

- [ ] 接入向量数据库（冷记忆）
- [ ] 实现多 Agent 并行协作
- [ ] 添加评测体系（Benchmark）
- [ ] 支持更多工具（代码执行、网页搜索等）