import requests
import json
import time

def test_login_nonexistent_user():
    """测试登录API，使用不存在的用户名"""
    url = "http://localhost:5001/auth/login"
    
    # 使用JSON数据
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    json_data = {
        "username": "nonexistent",
        "password": "password"
    }
    
    # 尝试连接，最多重试3次
    max_retries = 3
    retry_delay = 2  # 秒
    
    for attempt in range(max_retries):
        try:
            print(f"尝试 {attempt + 1}/{max_retries}...")
            # 发送JSON请求
            response = requests.post(url, headers=headers, json=json_data, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {response.headers}")
            print(f"Response Text: {response.text[:500]}...")
            
            try:
                json_result = response.json()
                print(f"JSON Response: {json.dumps(json_result, indent=2, ensure_ascii=False)}")
                # 成功获取响应，退出循环
                break
            except json.JSONDecodeError as e:
                print(f"Response is not valid JSON: {e}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                print("已达到最大重试次数，放弃尝试。")

if __name__ == "__main__":
    test_login_nonexistent_user() 