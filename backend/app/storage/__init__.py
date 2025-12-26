from .config_manager import get_platform_config, get_all_platforms

from .chat_history import (
    add_message, 
    load_chat, 
    get_all_sessions,
    get_session_info,
    delete_session,
    update_session_title,
)

__all__ = [
    # 配置管理
    'get_platform_config',
    'get_all_platforms',
    # 聊天记录管理
    'add_message',
    'load_chat',
    'get_all_sessions',
    'get_session_info',
    'delete_session',
    'update_session_title',
]