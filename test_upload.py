import requests
import json
from PIL import Image
from io import BytesIO

def create_test_image(width=100, height=100, color='rgb(255,0,0)'):
    """创建测试图片"""
    image = Image.new('RGB', (width, height), color=color)
    img_io = BytesIO()
    image.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return img_io

def main():
    # 创建会话
    s = requests.Session()
    s.headers.update({'Accept': 'application/json'})

    try:
        # 登录
        data = {
            "username": "test",
            "password": "test"
        }
        r = s.post("http://localhost:5000/auth/login", data=data)
        print(f"Login response: {r.text}")

        if r.status_code == 200 and r.json()['success']:
            # 测试文件上传
            img_io = create_test_image()
            files = {
                "file": ("test_image.jpg", img_io, "image/jpeg")
            }
            r = s.post("http://localhost:5000/admin/upload/", files=files)
            print(f"Upload response: {r.text}")

            # 如果上传成功，测试获取图片列表
            if r.status_code == 200:
                r = s.get("http://localhost:5000/admin/upload/images")
                print(f"Image list response: {r.text}")
        else:
            print("登录失败")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()