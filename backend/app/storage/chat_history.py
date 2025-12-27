import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import os

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_DIR = PROJECT_ROOT / 'data'
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = DB_DIR / 'chat_history.db'

def get_db_connection():
    """建立并返回一个数据库连接。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库，创建必要的表（如果不存在）。"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 创建聊天消息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                platform TEXT,
                model TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建会话元数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON chat_messages (session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON chat_messages (timestamp)')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_session_timestamp 
            ON chat_messages (session_id, timestamp)
        ''')
        
        conn.commit()

def add_message(session_id: str, role: str, content: str, platform: Optional[str] = None, model: Optional[str] = None):
    """
    向指定会话添加一条新的聊天记录。
    
    Args:
        session_id: 会话的唯一标识符
        role: 消息的角色 ('user', 'assistant', 'system')
        content: 消息内容
        platform: 可选，使用的平台
        model: 可选，使用的模型
        
    Returns:
        int: 新插入消息的 ID
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            'INSERT INTO chat_messages (session_id, role, content, platform, model) VALUES (?, ?, ?, ?, ?)',
            (session_id, role, content, platform, model)
        )
        message_id = cursor.lastrowid
        
        if role == 'user':
            existing = conn.execute(
                'SELECT title FROM chat_sessions WHERE session_id = ?',
                (session_id,)
            ).fetchone()
            
            if existing is None:
                title = content[:30] + ('...' if len(content) > 30 else '')
                conn.execute(
                    'INSERT INTO chat_sessions (session_id, title) VALUES (?, ?)',
                    (session_id, title)
                )
            else:
                conn.execute(
                    'UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?',
                    (session_id,)
                )
        else:
            conn.execute(
                '''INSERT INTO chat_sessions (session_id, title)
                   VALUES (?, '新对话')
                   ON CONFLICT(session_id) DO UPDATE SET updated_at = CURRENT_TIMESTAMP''',
                (session_id,)
            )
        
        conn.commit()
        return message_id
    
def load_chat(session_id: str, limit: Optional[int] = None):
    """
    从数据库加载一个会话的聊天记录。
    Args:
        session_id: 会话的唯一标识符
        limit: 可选，限制返回的消息数量（从最新的开始）
    Returns:
        List[Dict]: 包含消息字典的列表，按时间顺序排列
                   每个字典包含 'role', 'content', 'platform', 'model' 键
    """
    if limit:
        sql = '''
            SELECT role, content, platform, model FROM (
                SELECT role, content, platform, model, timestamp FROM chat_messages 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ) ORDER BY timestamp ASC
        '''
        params = (session_id, limit)
    else:
        sql = '''
            SELECT role, content, platform, model FROM chat_messages 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        '''
        params = (session_id,)
    
    with get_db_connection() as conn:
        cursor = conn.execute(sql, params)
        messages = [dict(row) for row in cursor.fetchall()]
    
    return messages

def get_all_sessions():
    """
    获取所有会话的列表，按最后更新时间降序排列。
    Returns:
        List[Dict]: 包含会话信息的列表，每个字典包含：
                   - session_id: 会话ID
                   - title: 会话标题
                   - created_at: 创建时间
                   - updated_at: 最后更新时间
                   - message_count: 消息数量
    """
    sql = '''
        SELECT 
            cs.session_id,
            cs.title,
            cs.created_at,
            cs.updated_at,
            COUNT(cm.id) as message_count
        FROM chat_sessions cs
        LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id
        GROUP BY cs.session_id
        ORDER BY cs.updated_at DESC
    '''
    
    with get_db_connection() as conn:
        cursor = conn.execute(sql)
        sessions = [dict(row) for row in cursor.fetchall()]
    
    return sessions
    
def delete_session(session_id: str):
    """
    删除指定会话的所有消息和元数据。
    
    Args:
        session_id: 要删除的会话ID
        
    Returns:
        bool: 删除是否成功
    """
    try:
        with get_db_connection() as conn:
            # 删除消息
            conn.execute('DELETE FROM chat_messages WHERE session_id = ?', (session_id,))
            # 删除会话元数据
            conn.execute('DELETE FROM chat_sessions WHERE session_id = ?', (session_id,))
            conn.commit()
        return True
    except Exception as e:
        print(f"删除会话失败: {e}")
        return False
    
def update_session_title(session_id: str, title: str):
    """
    更新会话的标题。
    Args:
        session_id: 会话ID
        title: 新标题
    Returns:
        bool: 更新是否成功
    """
    try:
        with get_db_connection() as conn:
            conn.execute(
                'UPDATE chat_sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?',
                (title, session_id)
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"更新标题失败: {e}")
        return False
