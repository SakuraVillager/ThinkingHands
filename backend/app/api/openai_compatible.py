from openai import OpenAI
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storage.config_manager import get_platform_config, get_all_platforms

load_dotenv()
    
def connect_OpenAICompatible(platform):
    """
    测试与平台的连接
    Args:
        platform: 平台名称
    
    Returns:
        dict: {
            "success": bool,
            "platform": str,
            "message": str,
            "models": list
        }
    """
    try:
        config = get_platform_config(platform)
        
        client = OpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"]
        )
        
        models = client.models.list()
        model_list = [model.id for model in models.data]
        
        return {
            "success": True,
            "platform": platform,
            "message": f"连接成功！找到 {len(model_list)} 个模型",
            "models": model_list
        }
    
    except ValueError as e:
        return {
            "success": False,
            "platform": platform,
            "message": f"配置错误: {str(e)}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "platform": platform,
            "message": f"连接失败: {str(e)}"
        }

def chat_OpenAICompatible(platform, user_prompt, model=None, system_prompt=None, max_tokens=None, temperature=None, top_p=None, frequency_penalty=None):
    config = get_platform_config(platform)

    api_key = config["api_key"]
    base_url = config["base_url"]
    model = model or config["model"]
    system_prompt = system_prompt or config["system_prompt"]
    max_tokens = max_tokens or config["max_tokens"]
    temperature = temperature or config["temperature"]
    top_p = top_p or config["top_p"]
    frequency_penalty = frequency_penalty or config["frequency_penalty"]
    extra_body = config.get("extra_body", {})

    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        stream=True,
        extra_body = extra_body
    )

    for chunk in response:
        if not chunk.choices:
            continue
        
        if chunk.choices[0].delta.content:
            yield {"type": "content", "data": chunk.choices[0].delta.content}
        
        if hasattr(chunk.choices[0].delta, 'reasoning_content') and \
            chunk.choices[0].delta.reasoning_content:
            yield {"type": "reasoning", "data": chunk.choices[0].delta.reasoning_content}

if __name__ == "__main__":

    platform = "siliconflow"
    model = get_platform_config(platform)["model"]
    
    run = True

    while run:
        print("1.选择平台")
        print("2.选择模型")
        print("3.测试连接")
        print("4.开始聊天")
        choice = input("请输入选项编号: ")

        match choice:
            case "1":
                available_platforms = get_all_platforms()
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
                result = connect_OpenAICompatible(platform)
                if result["success"]:
                    print("可用模型列表:")
                    for i in range(len(result["models"])):
                        print(f"{i+1} {result['models'][i]}")
                    model = result['models'][int(input("请输入模型编号: ")) - 1]
                else:
                    print(result["message"])

            case "3":
                result = connect_OpenAICompatible(platform)
                print(result["message"])

            case "4":
                reasoning = ""
                content = ""
                for chunk in chat_OpenAICompatible("siliconflow", "你好"):
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
                print("\n")
            case "q":
                run = False