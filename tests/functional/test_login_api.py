import requests
import json
import time

def test_login_api():
    """测试登录API，使用表单数据和JSON数据两种方式"""
    url = "http://localhost:5000/auth/login"
    
    print("=== 测试登录API ===")
    
    # 1. 使用表单数据测试
    print("\n1. 使用表单数据测试:")
    form_data = {
        "username": "admin",
        "password": "password123",
        "remember_me": "true"
    }
    
    try:
        # 发送表单请求
        form_response = requests.post(url, data=form_data, timeout=10)
        print(f"表单请求状态码: {form_response.status_code}")
        print(f"表单请求响应头: {dict(form_response.headers)}")
        print(f"表单请求响应内容: {form_response.text[:500]}...")
    except requests.exceptions.RequestException as e:
        print(f"表单请求失败: {e}")
    
    # 2. 使用JSON数据测试
    print("\n2. 使用JSON数据测试:")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    json_data = {
        "username": "admin",
        "password": "password123",
        "remember_me": True
    }
    
    try:
        # 发送JSON请求
        json_response = requests.post(url, headers=headers, json=json_data, timeout=10)
        print(f"JSON请求状态码: {json_response.status_code}")
        print(f"JSON请求响应头: {dict(json_response.headers)}")
        print(f"JSON请求响应内容: {json_response.text[:500]}...")
        
        try:
            json_result = json_response.json()
            print(f"JSON响应解析结果: {json.dumps(json_result, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError as e:
            print(f"响应不是有效的JSON: {e}")
    except requests.exceptions.RequestException as e:
        print(f"JSON请求失败: {e}")
    
    # 3. 使用不存在的用户测试
    print("\n3. 使用不存在的用户测试:")
    json_data_nonexistent = {
        "username": "nonexistent",
        "password": "password123"
    }
    
    try:
        # 发送JSON请求
        nonexistent_response = requests.post(url, headers=headers, json=json_data_nonexistent, timeout=10)
        print(f"不存在用户请求状态码: {nonexistent_response.status_code}")
        
        try:
            json_result = nonexistent_response.json()
            print(f"不存在用户响应解析结果: {json.dumps(json_result, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError as e:
            print(f"响应不是有效的JSON: {e}")
    except requests.exceptions.RequestException as e:
        print(f"不存在用户请求失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_login_api() 