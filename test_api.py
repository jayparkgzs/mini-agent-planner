import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("MODEL_NAME", "gpt-3.5-turbo")

print(f"API Key: {api_key[:15]}...")
print(f"Base URL: {base_url}")
print(f"Model: {model}")

try:
    client = OpenAI(api_key=api_key, base_url=base_url)
    # 增加超时到 60 秒
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "你好"}],
        max_tokens=50,
        timeout=60
    )
    print(f"\n✅ API 连接成功！")
    print(f"回复: {response.choices[0].message.content}")
except Exception as e:
    print(f"\n❌ API 连接失败: {type(e).__name__}")
    print(f"错误: {str(e)}")
