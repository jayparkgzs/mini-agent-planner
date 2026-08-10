import asyncio
import time
from typing import Dict, List
from dataclasses import dataclass

from scheduler.agents import SecurityAgent, PerformanceAgent, StyleAgent


@dataclass
class ReviewReport:
    pr_id: str
    overall_score: int
    status: str
    reviews: List[Dict]
    duration_ms: float
    summary: str


class CodeReviewPipeline:
    def __init__(self):
        self.security = SecurityAgent()
        self.performance = PerformanceAgent()
        self.style = StyleAgent()
    
    async def run(self, code: str, filename: str = "unknown", pr_id: str = "PR-001") -> ReviewReport:
        start = time.time()
        context = {
            "code": code,
            "filename": filename,
            "language": "python"
        }
        
        tasks = [
            asyncio.to_thread(self.security.review, context),
            asyncio.to_thread(self.performance.review, context),
            asyncio.to_thread(self.style.review, context)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        reviews = []
        for result in results:
            if isinstance(result, Exception):
                reviews.append({
                    "agent": "unknown",
                    "status": "error",
                    "score": 0,
                    "issues": [{"message": str(result)}],
                    "summary": f"❌ 审查出错: {str(result)}"
                })
            else:
                reviews.append(result)
        
        duration = (time.time() - start) * 1000
        
        total_score = sum(r.get("score", 0) for r in reviews) // len(reviews) if reviews else 0
        
        statuses = [r.get("status", "passed") for r in reviews]
        if "failed" in statuses:
            overall_status = "failed"
        elif "warning" in statuses:
            overall_status = "warning"
        else:
            overall_status = "passed"
        
        summary = self._generate_summary(reviews, total_score, sum(len(r.get("issues", [])) for r in reviews))
        
        return ReviewReport(
            pr_id=pr_id,
            overall_score=total_score,
            status=overall_status,
            reviews=reviews,
            duration_ms=duration,
            summary=summary
        )
    
    def _generate_summary(self, reviews: List[Dict], score: int, total_issues: int) -> str:
        lines = [
            f"## 代码审查报告",
            f"",
            f"**综合评分**: {score}/100",
            f"**审查结果**: {'✅ 通过' if score >= 80 else '⚠️ 警告' if score >= 60 else '❌ 不通过'}",
            f"**发现问题**: {total_issues} 个",
            f"",
            f"---",
            f""
        ]
        
        for review in reviews:
            agent = review.get("agent", "unknown").upper()
            status_icon = "✅" if review.get("status") == "passed" else "⚠️" if review.get("status") == "warning" else "❌"
            lines.append(f"### {status_icon} {agent} 审查（{review.get('score', 0)}分）")
            lines.append(f"{review.get('summary', '')}")
            lines.append("")
            
            for issue in review.get("issues", []):
                severity = issue.get("severity", "low")
                icon = "🔴" if severity == "high" else "🟡" if severity == "medium" else "🟢"
                lines.append(f"- {icon} **{severity.upper()}** 第{issue.get('line', '?')}行: {issue.get('message', '')}")
                lines.append(f"  > 💡 建议: {issue.get('suggest', '无')}")
                lines.append("")
        
        return "\n".join(lines)


pipeline = CodeReviewPipeline()