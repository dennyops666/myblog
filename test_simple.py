#!/bin/bash

import requests
import json

def test_login():
    """简单测试登录API"""
    print("测试登录API...")
    
    url = "http://localhost:5000/auth/login"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "username": "nonexistent",
        "password": "password"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {response.headers}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n测试完成")

if __name__ == "__main__":
    test_login() 