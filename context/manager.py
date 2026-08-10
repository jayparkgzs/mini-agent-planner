# context/manager.py
import re
from typing import List, Dict


class ContextManager:
    """
    上下文管理器：控制 Token 用量，防止超限
    策略：保留系统提示 + 最近 N 轮对话 + 关键记忆摘要
    """
    
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
    
    def build_messages(self, system_prompt: str, memory: List[Dict], current_input: str) -> List[Dict]:
        """
        构建消息列表，确保不超过 Token 预算
        """
        messages = [{"role": "system", "content": system_prompt}]
        used_tokens = self.estimate_tokens(system_prompt)
        
        # 从 memory 中选取最近对话，直到接近预算上限
        selected_memory = []
        for msg in reversed(memory):
            content = msg.get("content", "")
            msg_len = self.estimate_tokens(content)
            if used_tokens + msg_len > self.max_tokens * 0.8:
                break
            selected_memory.insert(0, msg)
            used_tokens += msg_len
        
        # 将 memory 转换为 messages 格式
        for msg in selected_memory:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ["user", "assistant"]:
                messages.append({"role": role, "content": content})
        
        # 添加当前输入
        messages.append({"role": "user", "content": current_input})
        
        return messages
    
    def estimate_tokens(self, text: str) -> int:
        """粗略估算 Token 数"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        return chinese_chars + int(english_words * 1.3)
