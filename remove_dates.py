import os
import re

def remove_creation_date(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # 移除包含"创建日期"的行
    new_lines = [line for line in lines if "创建日期" not in line]
    
    # 如果文件内容有变化，则写回文件
    if len(new_lines) != len(lines):
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(new_lines)
        print(f"已处理: {file_path}")

def process_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') or file.endswith('.py.bak'):
                file_path = os.path.join(root, file)
                remove_creation_date(file_path)

if __name__ == '__main__':
    # 处理主要目录
    process_directory('app')
    process_directory('tests')
    
    # 处理根目录的Python文件
    for file in ['run.py', 'init_db.py']:
        if os.path.exists(file):
            remove_creation_date(file)

print("处理完成！") 