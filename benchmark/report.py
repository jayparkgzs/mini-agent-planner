# benchmark/report.py
from benchmark.evaluator import AgentEvaluator, EvalResult


def print_report(evaluator: AgentEvaluator):
    """打印评测报告"""
    summary = evaluator.get_summary()
    
    print("=" * 50)
    print("Agent 评测报告")
    print("=" * 50)
    print(f"总任务数: {summary['total_tasks']}")
    print(f"成功率: {summary['success_rate']*100:.1f}%")
    print(f"工具调用准确率: {summary['tool_accuracy']*100:.1f}%")
    print(f"平均耗时: {summary['avg_duration_ms']:.0f}ms")
    print(f"总成本: ¥{summary['total_cost']:.4f}")
    print("-" * 50)
    print("详细结果:")
    for detail in summary['details']:
        status = "✅" if detail['success'] else "❌"
        print(f"{status} {detail['task_name']}: {detail['steps']}步, {detail['duration_ms']:.0f}ms")
    print("=" * 50)