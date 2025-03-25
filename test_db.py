import os
import sqlite3

def test_db_connection():
    """测试数据库连接"""
    db_path = '/data/myblog/instance/blog-dev.db'
    print(f"数据库文件路径: {db_path}")
    print(f"数据库文件是否存在: {os.path.exists(db_path)}")
    
    try:
        # 尝试连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 执行简单查询
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"数据库连接成功")
        print(f"数据库表: {tables}")
        
        # 关闭连接
        conn.close()
    except Exception as e:
        print(f"数据库连接失败: {e}")

if __name__ == "__main__":
    test_db_connection() 