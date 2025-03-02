"""
数据安全测试
"""

import pytest
from app.models import Post, Comment, User
from app.services.security import SecurityService
from app.extensions import db
import os

@pytest.fixture
def security_service():
    return SecurityService()

class TestXSSProtection:
    """XSS防护测试 [ST-003]"""

    def test_markdown_xss_protection(self, security_service):
        """测试Markdown XSS防护"""
        xss_markdown = [
            # 基本XSS尝试
            """<script>alert('xss')</script>""",
            # 图片XSS
            """![](javascript:alert('xss'))""",
            # 链接XSS
            """[click](javascript:alert('xss'))""",
            # HTML注入
            """<img src="x" onerror="alert('xss')">""",
        ]

        for content in xss_markdown:
            safe_html = security_service.sanitize_markdown(content)
            assert '<script>' not in safe_html
            assert 'javascript:' not in safe_html
            assert 'onerror=' not in safe_html

    def test_comment_xss_protection(self, security_service):
        """测试评论XSS防护"""
        xss_comments = [
            "<p onclick=alert('xss')>Hello</p>",
            "<a href='javascript:alert(1)'>click me</a>",
            "<img src=x onerror=alert('xss')>",
        ]

        for comment in xss_comments:
            safe_comment = security_service.sanitize_comment(comment)
            assert 'onclick=' not in safe_comment
            assert 'javascript:' not in safe_comment
            assert 'onerror=' not in safe_comment

    def test_input_filtering(self, security_service):
        """测试输入过滤"""
        dangerous_inputs = [
            {'name': '<script>alert(1)</script>'},
            {'email': '" onclick="alert(1)'},
            {'content': '<iframe src="evil.com">'},
        ]

        for input_data in dangerous_inputs:
            safe_data = security_service.sanitize_input(input_data)
            for key, value in safe_data.items():
                assert '<' not in value
                assert '>' not in value
                assert 'script' not in value.lower()


class TestCSRFProtection:
    """CSRF防护测试 [ST-004]"""

    def test_form_csrf_protection(self, test_client):
        """测试表单CSRF保护"""
        # 获取CSRF令牌
        response = test_client.get('/login')
        assert 'csrf_token' in response.data.decode()

        # 不带令牌的POST请求
        response = test_client.post('/login', data={
            'username': 'test',
            'password': 'password'
        })
        assert response.status_code == 400  # CSRF验证失败

        # 带无效令牌的POST请求
        response = test_client.post('/login', data={
            'username': 'test',
            'password': 'password',
            'csrf_token': 'invalid'
        })
        assert response.status_code == 400  # CSRF验证失败

    def test_api_csrf_protection(self, test_client):
        """测试API CSRF保护"""
        # API请求必须包含正确的CSRF头
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        response = test_client.post('/api/posts', json={
            'title': 'Test Post',
            'content': 'Content'
        }, headers=headers)
        assert response.status_code == 400  # 缺少CSRF令牌

        # 测试CORS预检请求
        response = test_client.options('/api/posts')
        assert 'Access-Control-Allow-Origin' in response.headers
        assert 'Access-Control-Allow-Methods' in response.headers
        assert 'Access-Control-Allow-Headers' in response.headers


class TestInjectionProtection:
    """注入防护测试 [ST-005]"""

    def test_sql_injection_protection(self, security_service, test_client):
        """测试SQL注入防护"""
        data = "'; DROP TABLE users; --"
        response = test_client.post('/test/sql', json={'data': data})
        assert response.status_code == 400

    def test_command_injection_protection(self, security_service):
        """测试命令注入防护"""
        dangerous_commands = [
            "file.txt; rm -rf /",
            "image.jpg && echo 'pwned'",
            "doc.pdf | cat /etc/passwd",
        ]

        for filename in dangerous_commands:
            safe_filename = security_service.sanitize_filename(filename)
            assert ';' not in safe_filename
            assert '&' not in safe_filename
            assert '|' not in safe_filename
            assert ' ' not in safe_filename

    def test_file_upload_vulnerability(self, security_service, test_client):
        """测试文件上传漏洞防护"""
        # 测试文件类型验证
        dangerous_files = [
            ('file.php', b'<?php echo "hack"; ?>'),
            ('file.jsp', b'<% Runtime.exec("/bin/bash -c ls"); %>'),
            ('file.exe', b'MZ\x90\x00\x03\x00\x00\x00'),
        ]

        for filename, content in dangerous_files:
            response = test_client.post('/upload', data={
                'file': (content, filename)
            })
            assert response.status_code == 400  # 文件类型不允许

        # 测试文件大小限制
        large_file = ('large.txt', b'0' * (10 * 1024 * 1024))  # 10MB
        response = test_client.post('/upload', data={
            'file': large_file
        })
        assert response.status_code == 400  # 文件太大

        # 测试文件内容验证
        malicious_image = ('image.jpg', b'<?php echo "hack"; ?>')
        response = test_client.post('/upload', data={
            'file': malicious_image
        })
        assert response.status_code == 400  # 文件内容无效

def test_xss_protection(test_client):
    """测试XSS防护"""
    data = '<script>alert("xss")</script>'
    response = test_client.post('/test/xss', json={'data': data})
    assert response.status_code == 200
    assert '<script>' not in response.json['data'] 