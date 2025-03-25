#!/usr/bin/env python3
"""
检查应用的运行状态
"""
import os
import sys
import subprocess
import socket
import time

def check_process():
    """检查gunicorn进程"""
    try:
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        output = result.stdout
        
        gunicorn_processes = [line for line in output.split("\n") if "gunicorn" in line]
        print(f"找到 {len(gunicorn_processes)} 个 gunicorn 进程:")
        for process in gunicorn_processes:
            print(f"  {process}")
        
        return len(gunicorn_processes) > 0
    except Exception as e:
        print(f"检查进程时出错: {str(e)}")
        return False

def check_port():
    """检查5000端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 5000))
    sock.close()
    
    if result == 0:
        print("端口 5000 已开放")
        return True
    else:
        print("端口 5000 未开放")
        return False

def check_response():
    """检查应用响应"""
    try:
        import requests
        
        urls = [
            "http://localhost:5000/",
            "http://localhost:5000/blog/archive",
            "http://localhost:5000/blog/archive_test"
        ]
        
        for url in urls:
            try:
                print(f"\n检查URL: {url}")
                start_time = time.time()
                response = requests.get(url, timeout=5)
                duration = time.time() - start_time
                
                print(f"  状态码: {response.status_code}")
                print(f"  响应时间: {duration:.2f}秒")
                print(f"  内容长度: {len(response.content)} 字节")
                
                if response.status_code != 200:
                    print("  警告: 非200响应")
                
                # 检查是否有错误消息
                if b"error" in response.content.lower() or b"\u9519\u8bef" in response.content.lower():
                    print("  警告: 响应包含错误信息")
                
            except Exception as e:
                print(f"  请求失败: {str(e)}")
    
    except ImportError:
        print("未安装requests模块，跳过HTTP检查")
        return False

def check_logs():
    """检查日志文件"""
    log_files = [
        "/data/myblog/logs/myblog.log",
        "/data/myblog/logs/error.log"
    ]
    
    for log_file in log_files:
        print(f"\n检查日志文件: {log_file}")
        
        if not os.path.exists(log_file):
            print(f"  日志文件不存在")
            continue
        
        try:
            # 获取文件大小
            size = os.path.getsize(log_file)
            print(f"  文件大小: {size/1024:.2f} KB")
            
            # 获取最后修改时间
            mtime = os.path.getmtime(log_file)
            print(f"  最后修改时间: {time.ctime(mtime)}")
            
            # 读取最后10行
            result = subprocess.run(
                ["tail", "-n", "10", log_file], 
                capture_output=True, 
                text=True, 
                check=True
            )
            print("  最后10行内容:")
            for line in result.stdout.split("\n"):
                print(f"    {line}")
        
        except Exception as e:
            print(f"  检查日志出错: {str(e)}")

def main():
    """主函数"""
    print("===== 应用状态检查 =====")
    
    print("\n1. 检查gunicorn进程")
    process_ok = check_process()
    
    print("\n2. 检查端口状态")
    port_ok = check_port()
    
    print("\n3. 检查HTTP响应")
    check_response()
    
    print("\n4. 检查日志文件")
    check_logs()
    
    print("\n===== 检查结果 =====")
    if process_ok and port_ok:
        print("应用似乎正在运行，但可能存在其他问题")
    else:
        print("应用可能没有正常运行")
        print("建议执行: /data/myblog/manage.sh restart")

if __name__ == "__main__":
    main() 