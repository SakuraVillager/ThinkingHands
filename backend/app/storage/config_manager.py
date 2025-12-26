import json
import os
import shutil
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DEFAULT_PATH = PROJECT_ROOT / 'config_default.json'
CONFIG_PATH = PROJECT_ROOT / 'config.json'

def _ensure_config_exists():
    """首次运行时从 default 复制配置"""
    if not CONFIG_PATH.exists() and CONFIG_DEFAULT_PATH.exists():
        shutil.copy(CONFIG_DEFAULT_PATH, CONFIG_PATH)

def _load_config():
    """加载配置文件"""
    _ensure_config_exists()
    
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"配置文件不存在: {CONFIG_PATH}")
    except json.JSONDecodeError as e:
        raise ValueError(f"配置文件格式错误: {e}")

def get_platform_config(platform: str):
    """
    从 config.json 读取配置并从环境变量读取 API key
    Args:
        platform: 平台名称
    Returns:
        dict: 包含完整配置的字典（包括 api_key）
    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: 平台不存在、环境变量未设置或配置格式错误
    """
    all_configs = _load_config()
    
    if platform not in all_configs:
        raise ValueError(f"平台 '{platform}' 不存在于配置文件中")
    
    config = all_configs[platform].copy()
    
    env_name = f"{platform.upper()}_API_TOKEN"
    api_key = os.getenv(env_name)
    if not api_key:
        raise ValueError(f"环境变量 '{env_name}' 未设置")
    
    config["api_key"] = api_key
    return config

def get_all_platforms():
    """获取所有可用平台列表"""
    config_data = _load_config()
    return list(config_data.keys())