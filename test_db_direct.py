import sqlite3
import os

def test_db_connection():
    """测试直接连接数据库"""
    print("测试直接连接数据库...")
    
    db_path = '/data/myblog/instance/blog-dev.db'
    print(f"数据库文件路径: {db_path}")
    print(f"数据库文件是否存在: {os.path.exists(db_path)}")
    print(f"数据库文件大小: {os.path.getsize(db_path) if os.path.exists(db_path) else 'N/A'}")
    print(f"数据库文件权限: {oct(os.stat(db_path).st_mode)[-3:] if os.path.exists(db_path) else 'N/A'}")
    
    try:
        # 尝试连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 执行简单查询
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"数据库连接成功")
        print(f"数据库表: {tables}")
        
        # 查询用户表
        cursor.execute("SELECT id, username, email FROM users LIMIT 5;")
        users = cursor.fetchall()
        print(f"用户数据: {users}")
        
        # 关闭连接
        conn.close()
    except Exception as e:
        print(f"数据库连接失败: {e}")
    
    print("\n测试完成")

if __name__ == "__main__":
    test_db_connection() 