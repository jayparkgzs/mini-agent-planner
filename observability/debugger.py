from typing import Dict, List


class AgentDebugger:
    """
    Agent 故障诊断器
    根据追踪记录分析最可能的失败原因
    """
    
    # 失败模式知识库
    FAILURE_PATTERNS = {
        "model_hallucination": {
            "keywords": ["不确定", "可能", "也许", "我猜", "没有相关信息"],
            "category": "模型能力",
            "suggest": "增加系统提示的约束，或使用更强模型"
        },
        "prompt_ambiguous": {
            "keywords": ["无法理解", "不清楚", "请提供更多"],
            "category": "Prompt设计",
            "suggest": "优化用户指令，增加示例（Few-shot）"
        },
        "tool_not_found": {
            "keywords": ["找不到工具", "tool not found", "没有该工具"],
            "category": "工具链路",
            "suggest": "检查工具名称拼写，确认工具已注册"
        },
        "api_timeout": {
            "keywords": ["timeout", "timed out", "连接超时"],
            "category": "工具链路",
            "suggest": "增加超时时间，或检查网络/API可用性"
        },
        "context_overflow": {
            "keywords": ["token", "too long", "maximum context"],
            "category": "系统架构",
            "suggest": "启用上下文截断策略，或使用摘要机制"
        },
        "invalid_parameters": {
            "keywords": ["参数错误", "missing", "required", "invalid"],
            "category": "工具链路",
            "suggest": "检查工具 schema 定义，确保参数完整"
        }
    }
    
    def analyze(self, trace: Dict) -> Dict:
        """
        分析一次追踪，定位失败根因
        """
        if not trace or trace.get("status") == "completed":
            return {"status": "ok", "message": "任务成功完成"}
        
        # 收集所有错误信息
        errors = []
        for step in trace.get("steps", []):
            if step.get("error"):
                errors.append(step["error"])
            if step.get("observation") and "错误" in str(step["observation"]):
                errors.append(step["observation"])
        
        # 匹配失败模式
        matched_patterns = []
        for error in errors:
            error_str = str(error).lower()
            for pattern_name, pattern in self.FAILURE_PATTERNS.items():
                for keyword in pattern["keywords"]:
                    if keyword.lower() in error_str:
                        matched_patterns.append({
                            "pattern": pattern_name,
                            "category": pattern["category"],
                            "matched_keyword": keyword,
                            "suggest": pattern["suggest"]
                        })
                        break
        
        # 去重
        seen = set()
        unique_patterns = []
        for p in matched_patterns:
            key = p["pattern"]
            if key not in seen:
                seen.add(key)
                unique_patterns.append(p)
        
        # 生成诊断报告
        if unique_patterns:
            root_cause = unique_patterns[0]  # 取第一个匹配
            return {
                "status": "diagnosed",
                "trace_id": trace.get("trace_id"),
                "failure_category": root_cause["category"],
                "root_cause": root_cause["pattern"],
                "suggestion": root_cause["suggest"],
                "all_matches": unique_patterns,
                "errors": errors
            }
        
        return {
            "status": "unknown",
            "trace_id": trace.get("trace_id"),
            "message": "无法匹配已知失败模式，需要人工分析",
            "errors": errors
        }
    
    def analyze_all_failures(self, traces: List[Dict]) -> Dict:
        """分析所有失败追踪，生成统计报告"""
        failures = [t for t in traces if t.get("status") != "completed"]
        
        category_count = {}
        pattern_count = {}
        
        for trace in failures:
            diagnosis = self.analyze(trace)
            if diagnosis["status"] == "diagnosed":
                cat = diagnosis["failure_category"]
                category_count[cat] = category_count.get(cat, 0) + 1
                
                pattern = diagnosis["root_cause"]
                pattern_count[pattern] = pattern_count.get(pattern, 0) + 1
        
        return {
            "total_failures": len(failures),
            "category_distribution": category_count,
            "pattern_distribution": pattern_count,
            "top_issue": max(pattern_count, key=pattern_count.get) if pattern_count else "无"
        }