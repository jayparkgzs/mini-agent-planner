import re
from typing import Dict, List


class SecurityAgent:
    """安全审查 Agent：检测漏洞、密钥泄露、注入攻击"""
    
    def review(self, context: Dict) -> Dict:
        code = context.get("code", "")
        issues: List[Dict] = []
        
        if re.search(r'\beval\s*\(', code):
            issues.append({
                "severity": "high",
                "line": self._find_line(code, "eval("),
                "message": "发现 eval() 调用，存在代码注入风险",
                "suggest": "使用 ast.literal_eval 替代，或重构逻辑"
            })
        
        if re.search(r'(password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']', code, re.I):
            issues.append({
                "severity": "high",
                "line": self._find_line(code, "password"),
                "message": "发现硬编码凭证",
                "suggest": "使用环境变量或密钥管理服务"
            })
        
        if "http://" in code and "https://" not in code:
            issues.append({
                "severity": "medium",
                "line": self._find_line(code, "http://"),
                "message": "使用不安全的 HTTP 协议",
                "suggest": "统一使用 HTTPS"
            })
        
        return self._format_result("security", issues)
    
    def _find_line(self, code: str, pattern: str) -> int:
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if pattern in line:
                return i
        return 0
    
    def _format_result(self, agent_name: str, issues: List[Dict]) -> Dict:
        if not issues:
            return {
                "agent": agent_name,
                "status": "passed",
                "score": 100,
                "issues": [],
                "summary": "✅ 未发现安全问题"
            }
        
        score = 100
        for issue in issues:
            if issue["severity"] == "high":
                score -= 30
            elif issue["severity"] == "medium":
                score -= 15
            else:
                score -= 5
        
        return {
            "agent": agent_name,
            "status": "warning" if score >= 60 else "failed",
            "score": max(0, score),
            "issues": issues,
            "summary": f"⚠️ 发现 {len(issues)} 个问题"
        }


class PerformanceAgent:
    """性能审查 Agent"""
    
    def review(self, context: Dict) -> Dict:
        code = context.get("code", "")
        issues: List[Dict] = []
        
        if re.search(r'for\s+\w+\s+in\s+\w+.*:\s*\n.*\.filter\(', code):
            issues.append({
                "severity": "medium",
                "line": self._find_line(code, "for "),
                "message": "疑似 N+1 查询问题",
                "suggest": "使用 select_related() 或 prefetch_related() 优化"
            })
        
        if "SELECT *" in code.upper():
            issues.append({
                "severity": "low",
                "line": self._find_line(code, "SELECT *"),
                "message": "使用 SELECT * 查询不必要字段",
                "suggest": "只查询需要的字段"
            })
        
        return self._format_result("performance", issues)
    
    def _find_line(self, code: str, pattern: str) -> int:
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if pattern in line:
                return i
        return 0
    
    def _format_result(self, agent_name: str, issues: List[Dict]) -> Dict:
        if not issues:
            return {
                "agent": agent_name,
                "status": "passed",
                "score": 100,
                "issues": [],
                "summary": "✅ 未发现性能问题"
            }
        
        score = 100
        for issue in issues:
            if issue["severity"] == "high":
                score -= 25
            elif issue["severity"] == "medium":
                score -= 10
            else:
                score -= 5
        
        return {
            "agent": agent_name,
            "status": "warning" if score >= 60 else "failed",
            "score": max(0, score),
            "issues": issues,
            "summary": f"💡 发现 {len(issues)} 个优化建议"
        }


class StyleAgent:
    """规范审查 Agent"""
    
    def review(self, context: Dict) -> Dict:
        code = context.get("code", "")
        language = context.get("language", "python")
        issues: List[Dict] = []
        
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            if '\t' in line and language == "python":
                issues.append({
                    "severity": "low",
                    "line": i,
                    "message": "使用 Tab 缩进",
                    "suggest": "统一使用 4 个空格缩进"
                })
                break
        
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                issues.append({
                    "severity": "low",
                    "line": i,
                    "message": f"行长度 {len(line)} 超过建议值",
                    "suggest": "拆分为多行，保持每行 < 80 字符"
                })
                break
        
        func_names = re.findall(r'def\s+([A-Z][a-zA-Z0-9_]*)\s*\(', code)
        for name in func_names:
            issues.append({
                "severity": "low",
                "line": self._find_line(code, f"def {name}"),
                "message": f"函数名 '{name}' 使用大驼峰",
                "suggest": "Python 函数应使用 snake_case"
            })
        
        return self._format_result("style", issues)
    
    def _find_line(self, code: str, pattern: str) -> int:
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if pattern in line:
                return i
        return 0
    
    def _format_result(self, agent_name: str, issues: List[Dict]) -> Dict:
        if not issues:
            return {
                "agent": agent_name,
                "status": "passed",
                "score": 100,
                "issues": [],
                "summary": "✅ 代码规范良好"
            }
        
        score = 100 - len(issues) * 5
        return {
            "agent": agent_name,
            "status": "warning" if score >= 80 else "failed",
            "score": max(0, score),
            "issues": issues,
            "summary": f"💡 发现 {len(issues)} 个风格问题"
        }