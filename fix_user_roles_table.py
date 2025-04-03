#!/usr/bin/env python3
"""
修复user_roles表结构，添加缺失的created_at列
"""
import os
import sys
import logging
import sqlite3
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/data/myblog/logs/fix_user_roles.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fix_user_roles')

# 数据库路径
DB_PATH = '/data/myblog/instance/blog-dev.db'

def fix_user_roles_table():
    """修复user_roles表，添加缺失的created_at列"""
    try:
        logger.info("连接到数据库")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(user_roles)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        logger.info(f"当前user_roles表列: {column_names}")
        
        # 检查是否有created_at列
        if 'created_at' not in column_names:
            logger.info("user_roles表中缺少created_at列，正在重建表...")
            
            # 创建临时表
            cursor.execute("""
            CREATE TABLE user_roles_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role_id INTEGER,
                created_at TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(role_id) REFERENCES roles(id),
                UNIQUE(user_id, role_id)
            )
            """)
            
            # 获取当前时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 复制数据并设置created_at
            cursor.execute("""
            INSERT INTO user_roles_temp (id, user_id, role_id, created_at)
            SELECT id, user_id, role_id, ? FROM user_roles
            """, (current_time,))
            
            # 删除旧表并重命名临时表
            cursor.execute("DROP TABLE user_roles")
            cursor.execute("ALTER TABLE user_roles_temp RENAME TO user_roles")
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id)")
            
            conn.commit()
            logger.info(f"已成功重建user_roles表并添加created_at列，当前时间: {current_time}")
        else:
            logger.info("user_roles表已包含created_at列，无需修复")
        
        # 验证修复结果
        cursor.execute("PRAGMA table_info(user_roles)")
        columns_after = cursor.fetchall()
        column_names_after = [col[1] for col in columns_after]
        logger.info(f"修复后的user_roles表列: {column_names_after}")
        
        conn.close()
        logger.info("user_roles表修复完成")
        return True
    except Exception as e:
        logger.error(f"修复user_roles表时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False

if __name__ == "__main__":
    logger.info("开始修复user_roles表")
    
    if fix_user_roles_table():
        logger.info("修复user_roles表成功")
        logger.info("请重启应用以应用更改")
    else:
        logger.error("修复user_roles表失败") 