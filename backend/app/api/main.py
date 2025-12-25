from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("SILICONFLOW_API_TOKEN"), 
                base_url="https://api.siliconflow.cn/v1")
response = client.chat.completions.create(
    model="THUDM/GLM-4-9B-0414",
    messages=[
        {'role': 'user', 
        'content': "你好"}
    ],
    stream=True
)

for chunk in response:
    if not chunk.choices:
        continue
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
    if chunk.choices[0].delta.reasoning_content:
        print(chunk.choices[0].delta.reasoning_content, end="", flush=True)