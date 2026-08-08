# memory/short_term.py
import json
import os
from typing import List, Dict
from datetime import datetime


class ShortTermMemory:
    """短期记忆：保存当前会话的交互记录"""
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.memory_file = f"memory_{session_id}.json"
        self.messages: List[Dict] = []
        self._load()
    
    def _load(self):
        """从文件加载历史"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.messages = json.load(f)
            except:
                self.messages = []
    
    def add(self, role: str, content: str):
        """添加一条记录"""
        self.messages.append({
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content
        })
        self._save()
    
    def get_recent(self, n: int = 5) -> List[Dict]:
        """获取最近 n 条"""
        return self.messages[-n:]
    
    def clear(self):
        """清空记忆"""
        self.messages = []
        self._save()
    
    def _save(self):
        """保存到文件"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=2)