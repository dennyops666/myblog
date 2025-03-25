import requests
import json

def test_api():
    """测试不依赖数据库的API"""
    print("测试不依赖数据库的API...")
    
    url = "http://localhost:5002/api/test"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "username": "test",
        "password": "password"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {response.headers}")
        print(f"响应内容: {response.text}")
        
        try:
            json_result = response.json()
            print(f"JSON Response: {json.dumps(json_result, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError as e:
            print(f"Response is not valid JSON: {e}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n测试完成")

if __name__ == "__main__":
    test_api() 