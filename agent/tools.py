# agent/tools.py
import json
from typing import Callable, Dict, Any, List


class ToolRegistry:
    """工具注册中心：所有工具都在这里登记"""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: List[Dict] = []
    
    def register(self, name: str, description: str, parameters: Dict):
        """装饰器：注册一个工具"""
        def decorator(func: Callable):
            self._tools[name] = func
            self._schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": parameters,
                        "required": list(parameters.keys())
                    }
                }
            })
            return func
        return decorator
    
    def get_schemas(self) -> List[Dict]:
        """返回所有工具的定义（给 LLM 看的）"""
        return self._schemas
    
    def execute(self, name: str, arguments: Dict) -> str:
        """执行工具，返回字符串结果"""
        tool = self._tools.get(name)
        if not tool:
            return f"错误：找不到工具 '{name}'"
        try:
            result = tool(**arguments)
            return str(result)
        except Exception as e:
            return f"工具执行错误：{str(e)}"


# 创建全局注册表（整个项目共用这一个）
registry = ToolRegistry()


# ============ 下面定义具体工具 ============

@registry.register(
    name="search_weather",
    description="查询指定城市的天气信息",
    parameters={
        "city": {"type": "string", "description": "城市名称，如'北京'"}
    }
)
def search_weather(city: str) -> str:
    """模拟天气查询"""
    weather_db = {
        "北京": "晴天，25°C，空气质量良",
        "上海": "多云，28°C，空气质量优",
        "广州": "小雨，30°C，空气质量良",
        "深圳": "雷阵雨，29°C，空气质量优"
    }
    return weather_db.get(city, f"未找到 {city} 的天气信息")


@registry.register(
    name="calculator",
    description="执行数学计算",
    parameters={
        "expression": {"type": "string", "description": "数学表达式，如'2+3*4'"}
    }
)
def calculator(expression: str) -> str:
    """安全计算器"""
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "错误：表达式包含非法字符"
    try:
        result = eval(expression)
        return f"计算结果：{result}"
    except Exception as e:
        return f"计算错误：{str(e)}"


@registry.register(
    name="read_file",
    description="读取文件内容",
    parameters={
        "filename": {"type": "string", "description": "文件名"}
    }
)
def read_file(filename: str) -> str:
    """读取文件"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"文件 '{filename}' 不存在"
    except Exception as e:
        return f"读取错误：{str(e)}"


@registry.register(
    name="write_file",
    description="将内容写入文件（⚠️ 危险操作，需要用户确认）",
    parameters={
        "filename": {"type": "string", "description": "文件名"},
        "content": {"type": "string", "description": "要写入的内容"}
    }
)
def write_file(filename: str, content: str) -> str:
    """写入文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"成功写入文件 '{filename}'"
    except Exception as e:
        return f"写入错误：{str(e)}"