# tests/test_agent.py
from agent.tools import registry


def test_weather_tool():
    """测试天气工具"""
    result = registry.execute("search_weather", {"city": "北京"})
    assert "北京" in result or "晴天" in result
    print("✅ weather 测试通过")


def test_calculator_tool():
    """测试计算器"""
    result = registry.execute("calculator", {"expression": "2+3*4"})
    assert "14" in result
    print("✅ calculator 测试通过")


def test_registry():
    """测试工具注册表"""
    schemas = registry.get_schemas()
    names = [s["function"]["name"] for s in schemas]
    assert "search_weather" in names
    assert "calculator" in names
    assert "write_file" in names
    print("✅ registry 测试通过")


if __name__ == "__main__":
    test_weather_tool()
    test_calculator_tool()
    test_registry()
    print("\n所有测试通过！")