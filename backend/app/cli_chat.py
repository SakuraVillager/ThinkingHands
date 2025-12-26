import sys
from pathlib import Path
import uuid
import re

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.storage import chat_history, config_manager
from app.api import openai_compatible

# 初始化数据库
chat_history.init_db()

# 全局状态
session_id = None
platform = "siliconflow"
model = config_manager.get_platform_config(platform)["model"]

def chat(session_id, platform, model):
    user_input = input("请输入你的问题: ")
    chat_history.add_message(session_id, "user", user_input)
    reasoning = ""
    content = ""
    for chunk in openai_compatible.chat_OpenAICompatible(platform, user_input):
        if chunk["type"] == "reasoning":
            if not reasoning:
                print("[思考中...]", flush=True)
            reasoning += chunk["data"]
            print(chunk["data"], end="", flush=True)
        elif chunk["type"] == "content":
            if not content:
                print("[思考结束]", flush=True)
            content += chunk["data"]
            print(chunk["data"], end="", flush=True)
    chat_history.add_message(session_id, "assistant", reasoning + content, platform=platform, model=model)


while True:
    print("1.选择平台")
    print("2.选择模型")
    print("3.测试连接")
    print("4.查询聊天记录(可继续对话)")
    print("5.开始新聊天")
    choice = input("请输入选项编号: ")
    match choice:
        case "1":
            available_platforms = config_manager.get_all_platforms()
            print("可用平台列表:")
            for i, p in enumerate(available_platforms, 1):
                print(f"  {i}. {p}")
            platform_input = input("请输入平台名称: ")
            if platform_input not in available_platforms:
                print(f"平台 '{platform_input}' 不存在")
            else:
                platform = platform_input
                print(f"已切换到平台: {platform}")

        case "2":
            print("使用平台"+platform+",可用模型如下:")
            result = openai_compatible.connect_OpenAICompatible(platform)
            if result["success"]:
                print("可用模型列表:")
                for i in range(len(result["models"])):
                    print(f"{i+1} {result['models'][i]}")
                model = result['models'][int(input("请输入模型编号: ")) - 1]
            else:
                print(result["message"])

        case "3":
            result = openai_compatible.connect_OpenAICompatible(platform)
            print(result["message"])

        case "4":
            print("查询到以下聊天记录:")
            sessions= chat_history.get_all_sessions()
            for i, s in enumerate(sessions, 1):
                print(f"{i}. [{s['session_id'][:8]}] {s['title']}")
            session_choice = int(input("请输入要继续的聊天记录编号: ")) - 1
            session_id = sessions[session_choice]['session_id']
            chat_history_info = chat_history.load_chat(session_id)
            for msg in chat_history_info:
                if msg['role'] == 'user':
                    print(f"[用户]: {msg['content']}")
                elif msg['role'] == 'assistant':
                    print(f"[ AI ] ({msg.get('platform','未知平台')}-{msg.get('model','未知模型')}): {msg['content']}")
            chat(session_id, platform, model)

        case "5":
            session_id = str(uuid.uuid4())
            print(f"{platform}平台-{model}模型")
            chat(session_id, platform, model)
            
        case "q":
            run = False
        
