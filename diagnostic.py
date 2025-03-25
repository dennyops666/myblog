#!/usr/bin/env python
"""
诊断脚本 - 用于测试博客系统中各种路由的可访问性
"""

import requests
import sys
import json
from urllib.parse import urljoin

def test_route(base_url, path, method='GET', data=None, headers=None, cookies=None):
    """测试指定的路由"""
    url = urljoin(base_url, path)
    print(f"\n测试路由: {method} {url}")
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, cookies=cookies, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, data=data, headers=headers, cookies=cookies, timeout=10)
        else:
            print(f"不支持的HTTP方法: {method}")
            return None
        
        print(f"状态码: {response.status_code}")
        print(f"内容类型: {response.headers.get('Content-Type', '未指定')}")
        print(f"内容长度: {len(response.text)} 字符")
        
        if 'text/html' in response.headers.get('Content-Type', ''):
            # 简单检测HTML页面返回的内容是错误页面还是正常页面
            if "404" in response.text and "Not Found" in response.text:
                print("返回了404页面")
            elif "500" in response.text and "Internal Server Error" in response.text:
                print("返回了500页面")
            elif "<html" in response.text:
                print("返回了HTML页面")
                if len(response.text) < 500:
                    print("内容预览:\n" + response.text)
                else:
                    print("内容预览 (前500字符):\n" + response.text[:500] + "...\n")
            else:
                print("内容预览:\n" + response.text)
        elif 'application/json' in response.headers.get('Content-Type', ''):
            try:
                json_data = response.json()
                print("JSON响应:\n" + json.dumps(json_data, indent=2, ensure_ascii=False))
            except:
                print("无法解析JSON响应")
                print("内容预览:\n" + response.text[:500] + "...\n" if len(response.text) > 500 else response.text)
        else:
            print("内容预览:\n" + response.text[:500] + "...\n" if len(response.text) > 500 else response.text)
        
        return response
    
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return None

def main():
    """主函数"""
    base_url = "http://localhost:5000"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"使用基础URL: {base_url}")
    
    # 测试路由列表
    routes = [
        "/",
        "/blog",
        "/admin",
        "/admin/",
        "/admin/dashboard",
        "/admin/post",
        "/admin/post/",
        "/admin/posts",
        "/debug/routes",
        "/admin_old"
    ]
    
    results = {}
    for route in routes:
        response = test_route(base_url, route)
        results[route] = {
            "status_code": response.status_code if response else None,
            "content_length": len(response.text) if response else 0,
            "content_type": response.headers.get('Content-Type', '未知') if response else '未知'
        }
    
    # 打印摘要
    print("\n\n===== 测试结果摘要 =====")
    for route, result in results.items():
        status = "✅ 成功" if result["status_code"] in (200, 302) else "❌ 失败"
        print(f"{status} {route} - 状态码: {result['status_code']}")
    
    # 检查是否有失败的路由
    failed_routes = [r for r, res in results.items() if not res["status_code"] or res["status_code"] not in (200, 302)]
    if failed_routes:
        print(f"\n失败的路由数: {len(failed_routes)}/{len(routes)}")
        print("失败的路由: " + ", ".join(failed_routes))
    else:
        print("\n所有路由测试通过!")

if __name__ == "__main__":
    main() 